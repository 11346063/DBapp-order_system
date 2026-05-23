from django.db import transaction
from django.db.models import Max

from web_app.models import Cart, CartItem, CartItemOption, Identity, Menu, Options
from web_app.services.exceptions import NotFoundError, PriceChangedError


def _resolve_context(user_or_session, session=None):
    if session is None:
        return None, user_or_session
    return user_or_session, session


def _uses_db_cart(user):
    return (
        user is not None
        and user.is_authenticated
        and user.identity == Identity.CUSTOMER
    )


def get_or_create_user_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def get_cart(user_or_session, session=None):
    user, session = _resolve_context(user_or_session, session)
    if _uses_db_cart(user):
        return _db_cart_items(user)
    return [_coerce_cart_item(item) for item in session.get("cart", [])]


def replace_cart(user_or_session, session_or_cart, cart=None):
    if cart is None:
        session = user_or_session
        cart = session_or_cart
        session["cart"] = cart
        return

    user = user_or_session
    session = session_or_cart
    if _uses_db_cart(user):
        _replace_db_cart(user, cart)
        return
    session["cart"] = cart


def clear_cart(user_or_session, session=None):
    user, session = _resolve_context(user_or_session, session)
    if _uses_db_cart(user):
        get_or_create_user_cart(user).items.all().delete()
        return
    session["cart"] = []


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


def _coerce_cart_item(item):
    options = item.get("options", [])
    base_price = item.get("base_price", item.get("price", 0))
    options_price = item.get("options_price", _option_price(options))
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


def add_item(user_or_session, session_or_data, data=None):
    user, session, data = _resolve_mutation_args(user_or_session, session_or_data, data)
    if _uses_db_cart(user):
        cart_item = _append_db_cart_item(user, data)
        return {"cart_count": cart_count(_db_cart_items(user)), "id": cart_item.pk}

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


def adjust_item(user_or_session, session_or_data, data=None):
    user, session, data = _resolve_mutation_args(user_or_session, session_or_data, data)
    if _uses_db_cart(user):
        return _adjust_db_item(user, data)

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


def update_item_quantity(
    user_or_session, session_or_index, index_or_quantity, quantity=None
):
    if quantity is None:
        session = user_or_session
        index = session_or_index
        quantity = index_or_quantity
        user = None
    else:
        user = user_or_session
        session = session_or_index
        index = index_or_quantity

    if _uses_db_cart(user):
        return _update_db_item_quantity(user, index, quantity)

    cart = get_cart(session)

    if 0 <= index < len(cart):
        if quantity <= 0:
            cart.pop(index)
        else:
            cart[index]["quantity"] = quantity
            cart[index]["subtotal"] = cart[index]["unit_price"] * quantity

    replace_cart(session, cart)
    return summarize_cart(cart)


def remove_item(user_or_session, session_or_index, index=None):
    if index is None:
        session = user_or_session
        index = session_or_index
        user = None
    else:
        user = user_or_session
        session = session_or_index

    if _uses_db_cart(user):
        return _remove_db_item(user, index)

    cart = get_cart(session)

    if 0 <= index < len(cart):
        cart.pop(index)

    replace_cart(session, cart)
    return summarize_cart(cart)


def remove_last_item_by_menu(user_or_session, session_or_menu_id, menu_id=None):
    if menu_id is None:
        session = user_or_session
        menu_id = session_or_menu_id
        user = None
    else:
        user = user_or_session
        session = session_or_menu_id

    if _uses_db_cart(user):
        return _remove_last_db_item_by_menu(user, menu_id)

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


def append_menu_item_to_cart(user, session, menu, quantity, options=None):
    if _uses_db_cart(user):
        data = {
            "menu_id": menu.pk,
            "name": menu.name,
            "price": menu.price,
            "quantity": quantity,
            "options": options or [],
        }
        _append_db_cart_item(user, data)
        return quantity

    cart = get_cart(session)
    append_menu_item(cart, menu, quantity, options)
    replace_cart(session, cart)
    return quantity


def merge_session_cart_to_db(user, session):
    if not _uses_db_cart(user):
        return {"merged": 0, "cart_count": cart_count(session.get("cart", []))}

    source_cart = [_coerce_cart_item(item) for item in session.get("cart", [])]
    merged = 0
    for item in source_cart:
        if not item.get("menu_id"):
            continue
        _append_db_cart_item(
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
    return {"merged": merged, "cart_count": cart_count(_db_cart_items(user))}


def validate_prices(user_or_session, session=None):
    user, session = _resolve_context(user_or_session, session)
    items = (
        get_cart(user, session) if session is not None else get_cart(user_or_session)
    )
    price_changes = []
    old_total = cart_total(items)
    new_total = 0

    for index, item in enumerate(items):
        latest = _latest_item_snapshot(item)
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


def sync_prices(user_or_session, session=None):
    user, session = _resolve_context(user_or_session, session)
    if _uses_db_cart(user):
        _sync_db_prices(user)
        cart = _db_cart_items(user)
    else:
        cart = get_cart(session)
        synced = [_latest_item_snapshot(item) for item in cart]
        replace_cart(session, synced)
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


def _resolve_mutation_args(user_or_session, session_or_data, data):
    if data is None:
        return None, user_or_session, session_or_data
    return user_or_session, session_or_data, data


def _db_cart_items(user):
    cart = get_or_create_user_cart(user)
    return [
        _serialize_cart_item(item)
        for item in cart.items.select_related("menu").prefetch_related("options__opt")
    ]


def _serialize_cart_item(item):
    return {
        "id": item.pk,
        "menu_id": item.menu_id,
        "name": item.menu.name,
        "base_price": item.base_price,
        "options": [
            {
                "id": option.opt_id,
                "name": option.name,
                "price": option.price,
                "level": option.level,
            }
            for option in item.options.all()
        ],
        "options_price": item.options_price,
        "unit_price": item.unit_price,
        "quantity": item.quantity,
        "subtotal": item.subtotal,
    }


def _replace_db_cart(user, cart_payload):
    cart = get_or_create_user_cart(user)
    with transaction.atomic():
        cart.items.all().delete()
        for item in cart_payload:
            _append_db_cart_item(user, _db_data_from_cart_item(item))


def _db_data_from_cart_item(item):
    return {
        "menu_id": item["menu_id"],
        "name": item["name"],
        "price": item["base_price"],
        "quantity": item["quantity"],
        "options": item.get("options", []),
    }


def _append_db_cart_item(user, data):
    try:
        menu = Menu.objects.get(pk=data["menu_id"])
    except Menu.DoesNotExist as exc:
        raise NotFoundError("找不到此餐點") from exc

    cart = get_or_create_user_cart(user)
    options = _normalize_options(data.get("options", []))
    base_price = menu.price
    options_price = _option_price(options)
    unit_price = base_price + options_price
    quantity = data["quantity"]
    next_order = (
        cart.items.aggregate(max_order=Max("sort_order"))["max_order"] or 0
    ) + 1

    with transaction.atomic():
        cart_item = CartItem.objects.create(
            cart=cart,
            menu=menu,
            quantity=quantity,
            base_price=base_price,
            options_price=options_price,
            unit_price=unit_price,
            subtotal=unit_price * quantity,
            sort_order=next_order,
        )
        for option in options:
            CartItemOption.objects.create(
                cart_item=cart_item,
                opt_id=option["id"],
                name=option["name"],
                price=option["price"],
                level=option.get("level", 1),
            )
    return cart_item


def _normalize_options(options):
    normalized = []
    for option in options:
        opt_id = option.get("id")
        if not opt_id:
            continue
        try:
            opt = Options.objects.get(pk=opt_id)
        except Options.DoesNotExist as exc:
            raise NotFoundError("找不到此選項") from exc
        normalized.append(
            {
                "id": opt.pk,
                "name": opt.name,
                "price": opt.price,
                "level": int(option.get("level", 1)),
            }
        )
    return normalized


def _adjust_db_item(user, data):
    cart = get_or_create_user_cart(user)
    item = cart.items.filter(menu_id=data["menu_id"], options__isnull=True).first()
    item_quantity = item.quantity if item else 0
    item_quantity = max(0, item_quantity + data["delta"])

    if item is None and item_quantity > 0:
        _append_db_cart_item(
            user,
            {
                "menu_id": data["menu_id"],
                "name": data["name"],
                "price": data["price"],
                "quantity": item_quantity,
                "options": [],
            },
        )
    elif item is not None and item_quantity <= 0:
        item.delete()
    elif item is not None:
        item.quantity = item_quantity
        item.subtotal = item.unit_price * item_quantity
        item.save(update_fields=["quantity", "subtotal", "updated_at"])

    return {
        "cart_count": cart_count(_db_cart_items(user)),
        "item_quantity": item_quantity,
    }


def _update_db_item_quantity(user, index, quantity):
    items = list(get_or_create_user_cart(user).items.all())
    if 0 <= index < len(items):
        item = items[index]
        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            item.subtotal = item.unit_price * quantity
            item.save(update_fields=["quantity", "subtotal", "updated_at"])
    return summarize_cart(_db_cart_items(user))


def _remove_db_item(user, index):
    items = list(get_or_create_user_cart(user).items.all())
    if 0 <= index < len(items):
        items[index].delete()
    return summarize_cart(_db_cart_items(user))


def _remove_last_db_item_by_menu(user, menu_id):
    cart = get_or_create_user_cart(user)
    item = cart.items.filter(menu_id=menu_id).order_by("-sort_order", "-id").first()
    if item:
        item.delete()
    items = _db_cart_items(user)
    return {
        "cart_count": cart_count(items),
        "item_quantity": sum(
            item["quantity"] for item in items if item["menu_id"] == menu_id
        ),
    }


def _latest_item_snapshot(item):
    try:
        menu = Menu.objects.get(pk=item["menu_id"])
    except Menu.DoesNotExist as exc:
        raise NotFoundError("找不到此餐點") from exc

    latest_options = []
    for option in item.get("options", []):
        opt_id = option.get("id")
        if not opt_id:
            continue
        try:
            opt = Options.objects.get(pk=opt_id)
        except Options.DoesNotExist as exc:
            raise NotFoundError("找不到此選項") from exc
        latest_options.append(
            {
                "id": opt.pk,
                "name": opt.name,
                "price": opt.price,
                "level": int(option.get("level", 1)),
            }
        )

    return build_cart_item(
        menu.pk,
        menu.name,
        menu.price,
        item["quantity"],
        latest_options,
    ) | {"id": item.get("id")}


def _has_price_change(item, latest):
    return (
        item["base_price"] != latest["base_price"]
        or item["options_price"] != latest["options_price"]
        or item["unit_price"] != latest["unit_price"]
        or item["subtotal"] != latest["subtotal"]
        or item.get("options", []) != latest.get("options", [])
    )


def _sync_db_prices(user):
    cart = get_or_create_user_cart(user)
    with transaction.atomic():
        for item in cart.items.select_related("menu").prefetch_related("options__opt"):
            latest = _latest_item_snapshot(_serialize_cart_item(item))
            item.base_price = latest["base_price"]
            item.options_price = latest["options_price"]
            item.unit_price = latest["unit_price"]
            item.subtotal = latest["subtotal"]
            item.save(
                update_fields=[
                    "base_price",
                    "options_price",
                    "unit_price",
                    "subtotal",
                    "updated_at",
                ]
            )

            existing = {option.opt_id: option for option in item.options.all()}
            for option_data in latest["options"]:
                option = existing.get(option_data["id"])
                if option is None:
                    CartItemOption.objects.create(
                        cart_item=item,
                        opt_id=option_data["id"],
                        name=option_data["name"],
                        price=option_data["price"],
                        level=option_data["level"],
                    )
                else:
                    option.name = option_data["name"]
                    option.price = option_data["price"]
                    option.level = option_data["level"]
                    option.save(update_fields=["name", "price", "level"])
