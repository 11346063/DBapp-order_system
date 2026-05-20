def get_cart(session):
    return session.get("cart", [])


def replace_cart(session, cart):
    session["cart"] = cart


def cart_count(cart):
    return sum(item["quantity"] for item in cart)


def cart_total(cart):
    return sum(item["subtotal"] for item in cart)


def summarize_cart(cart):
    return {"total": cart_total(cart), "cart_count": cart_count(cart)}


def _option_price(options):
    return sum(opt.get("price", 0) for opt in options)


def build_cart_item(menu_id, name, price, quantity, options=None):
    options = options or []
    options_price = _option_price(options)
    unit_price = price + options_price
    return {
        "menu_id": menu_id,
        "name": name,
        "base_price": price,
        "options": options,
        "options_price": options_price,
        "unit_price": unit_price,
        "quantity": quantity,
        "subtotal": unit_price * quantity,
    }


def add_item(session, data):
    cart = get_cart(session)
    cart.append(
        build_cart_item(
            data["menu_id"],
            data["name"],
            data["price"],
            data["quantity"],
            data["options"],
        )
    )
    replace_cart(session, cart)
    return {"cart_count": cart_count(cart)}


def adjust_item(session, data):
    cart = get_cart(session)
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

    replace_cart(session, cart)
    return {"cart_count": cart_count(cart), "item_quantity": item_quantity}


def update_item_quantity(session, index, quantity):
    cart = get_cart(session)

    if 0 <= index < len(cart):
        if quantity <= 0:
            cart.pop(index)
        else:
            cart[index]["quantity"] = quantity
            cart[index]["subtotal"] = cart[index]["unit_price"] * quantity

    replace_cart(session, cart)
    return summarize_cart(cart)


def remove_item(session, index):
    cart = get_cart(session)

    if 0 <= index < len(cart):
        cart.pop(index)

    replace_cart(session, cart)
    return summarize_cart(cart)


def remove_last_item_by_menu(session, menu_id):
    cart = get_cart(session)

    last_index = None
    for index in range(len(cart) - 1, -1, -1):
        if cart[index].get("menu_id") == menu_id:
            last_index = index
            break

    if last_index is not None:
        cart.pop(last_index)

    replace_cart(session, cart)
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
