from web_app.services import cart_db
from web_app.services._cart_utils import build_cart_item, option_price
from web_app.services.exceptions import PriceChangedError


def get_cart(user, session):
    if cart_db.uses_db_cart(user):
        return cart_db.cart_items(user)
    return [_coerce_cart_item(item) for item in session.get("cart", [])]


def replace_cart(user, session, cart):
    if cart_db.uses_db_cart(user):
        cart_db.replace_cart(user, cart)
        return
    session["cart"] = cart


def clear_cart(user, session):
    if cart_db.uses_db_cart(user):
        cart_db.clear_cart(user)
        return
    session["cart"] = []


def cart_count(cart):
    return sum(item["quantity"] for item in cart)


def cart_total(cart):
    return sum(item["subtotal"] for item in cart)


def summarize_cart(cart):
    return {"total": cart_total(cart), "cart_count": cart_count(cart)}


def _coerce_cart_item(item):
    options = item.get("options", [])
    base_price = item.get("base_price", item.get("price", 0))
    options_price = item.get("options_price", option_price(options))
    unit_price = item.get("unit_price", base_price + options_price)
    quantity = item.get("quantity", 1)
    return {
        "menu_id": item.get("menu_id"),
        "name": item.get("name", ""),
        "base_price": base_price,
        "options": options,
        "options_price": options_price,
        "unit_price": unit_price,
        "quantity": quantity,
        "subtotal": item.get("subtotal", unit_price * quantity),
    } | ({"id": item["id"]} if "id" in item else {})


def add_item(user, session, data):
    if cart_db.uses_db_cart(user):
        cart_item = cart_db.append_item(user, data)
        return {"cart_count": cart_count(cart_db.cart_items(user)), "id": cart_item.pk}

    cart = get_cart(user, session)
    cart.append(
        build_cart_item(
            data["menu_id"],
            data["name"],
            data["price"],
            data["quantity"],
            data["options"],
        )
    )
    replace_cart(user, session, cart)
    return {"cart_count": cart_count(cart)}


def adjust_item(user, session, data):
    if cart_db.uses_db_cart(user):
        return cart_db.adjust_item(user, data)

    cart = get_cart(user, session)
    target_index = None
    item_quantity = 0

    for index, item in enumerate(cart):
        if item.get("menu_id") == data["menu_id"] and item.get("options", []) == []:
            target_index = index
            item_quantity = item["quantity"]
            break

    item_quantity = max(0, item_quantity + data["delta"])

    if target_index is None and item_quantity > 0:
        cart.append(
            build_cart_item(
                data["menu_id"],
                data["name"],
                data["price"],
                item_quantity,
                [],
            )
        )
    elif target_index is not None and item_quantity <= 0:
        cart.pop(target_index)
    elif target_index is not None:
        cart[target_index]["quantity"] = item_quantity
        cart[target_index]["subtotal"] = (
            cart[target_index]["unit_price"] * item_quantity
        )

    replace_cart(user, session, cart)
    return {"cart_count": cart_count(cart), "item_quantity": item_quantity}


def update_item_quantity(user, session, index, quantity):
    if cart_db.uses_db_cart(user):
        return cart_db.update_item_quantity(user, index, quantity)

    cart = get_cart(user, session)

    if 0 <= index < len(cart):
        if quantity <= 0:
            cart.pop(index)
        else:
            cart[index]["quantity"] = quantity
            cart[index]["subtotal"] = cart[index]["unit_price"] * quantity

    replace_cart(user, session, cart)
    return summarize_cart(cart)


def remove_item(user, session, index):
    if cart_db.uses_db_cart(user):
        return cart_db.remove_item(user, index)

    cart = get_cart(user, session)

    if 0 <= index < len(cart):
        cart.pop(index)

    replace_cart(user, session, cart)
    return summarize_cart(cart)


def remove_last_item_by_menu(user, session, menu_id):
    if cart_db.uses_db_cart(user):
        return cart_db.remove_last_item_by_menu(user, menu_id)

    cart = get_cart(user, session)

    last_index = None
    for index in range(len(cart) - 1, -1, -1):
        if cart[index].get("menu_id") == menu_id:
            last_index = index
            break

    if last_index is not None:
        cart.pop(last_index)

    replace_cart(user, session, cart)
    return {
        "cart_count": cart_count(cart),
        "item_quantity": sum(
            item["quantity"] for item in cart if item.get("menu_id") == menu_id
        ),
    }


def append_menu_item(cart, menu, quantity, options=None):
    cart.append(
        build_cart_item(menu.pk, menu.name, menu.price, quantity, options or [])
    )
    return quantity


def append_menu_item_to_cart(user, session, menu, quantity, options=None):
    if cart_db.uses_db_cart(user):
        data = {
            "menu_id": menu.pk,
            "name": menu.name,
            "price": menu.price,
            "quantity": quantity,
            "options": options or [],
        }
        cart_db.append_item(user, data)
        return quantity

    cart = get_cart(user, session)
    append_menu_item(cart, menu, quantity, options)
    replace_cart(user, session, cart)
    return quantity


def merge_session_cart_to_db(user, session):
    if not cart_db.uses_db_cart(user):
        return {"merged": 0, "cart_count": cart_count(session.get("cart", []))}

    source_cart = [_coerce_cart_item(item) for item in session.get("cart", [])]
    merged = 0
    for item in source_cart:
        if not item.get("menu_id"):
            continue
        cart_db.append_item(
            user,
            {
                "menu_id": item["menu_id"],
                "name": item["name"],
                "price": item.get("base_price", item.get("price", 0)),
                "quantity": item["quantity"],
                "options": item.get("options", []),
            },
        )
        merged += item["quantity"]

    session["cart"] = []
    return {"merged": merged, "cart_count": cart_count(cart_db.cart_items(user))}


def validate_prices(user, session):
    items = get_cart(user, session)
    price_changes = []
    old_total = cart_total(items)
    new_total = 0

    for index, item in enumerate(items):
        latest = cart_db.latest_item_snapshot(item)
        new_total += latest["subtotal"]
        if _has_price_change(item, latest):
            price_changes.append(
                {
                    "cart_item_id": item.get("id"),
                    "index": index,
                    "name": item["name"],
                    "old_unit_price": item["unit_price"],
                    "new_unit_price": latest["unit_price"],
                    "quantity": item["quantity"],
                    "old_subtotal": item["subtotal"],
                    "new_subtotal": latest["subtotal"],
                }
            )

    return {
        "has_changes": bool(price_changes),
        "old_total": old_total,
        "new_total": new_total,
        "price_changes": price_changes,
    }


def sync_prices(user, session):
    if cart_db.uses_db_cart(user):
        cart_db.sync_prices(user)
        cart = cart_db.cart_items(user)
    else:
        cart = get_cart(user, session)
        synced = [cart_db.latest_item_snapshot(item) for item in cart]
        replace_cart(user, session, synced)
        cart = synced

    return {
        "total": cart_total(cart),
        "cart_count": cart_count(cart),
        "price_changes": [],
    }


def ensure_prices_current(user, session):
    result = validate_prices(user, session)
    if result["has_changes"]:
        raise PriceChangedError("部分餐點價格已更新，請確認最新價格後再送出")


def _has_price_change(item, latest):
    return (
        item["base_price"] != latest["base_price"]
        or item["options_price"] != latest["options_price"]
        or item["unit_price"] != latest["unit_price"]
        or item["subtotal"] != latest["subtotal"]
        or item.get("options", []) != latest.get("options", [])
    )
