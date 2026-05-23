from django.db import transaction
from django.db.models import Max

from web_app.models import Cart, CartItem, CartItemOption, Identity, Menu, Options
from web_app.services.exceptions import NotFoundError


def uses_db_cart(user):
    return (
        user is not None
        and user.is_authenticated
        and user.identity == Identity.CUSTOMER
    )


def get_or_create_user_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def cart_items(user):
    cart = get_or_create_user_cart(user)
    return [
        serialize_cart_item(item)
        for item in cart.items.select_related("menu").prefetch_related("options__opt")
    ]


def serialize_cart_item(item):
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


def replace_cart(user, cart_payload):
    cart = get_or_create_user_cart(user)
    with transaction.atomic():
        cart.items.all().delete()
        for item in cart_payload:
            append_item(user, _db_data_from_cart_item(item))


def clear_cart(user):
    get_or_create_user_cart(user).items.all().delete()


def append_item(user, data):
    try:
        menu = Menu.objects.get(pk=data["menu_id"])
    except Menu.DoesNotExist as exc:
        raise NotFoundError("找不到此餐點") from exc

    cart = get_or_create_user_cart(user)
    options = normalize_options(data.get("options", []))
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


def normalize_options(options):
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


def adjust_item(user, data):
    cart = get_or_create_user_cart(user)
    item = cart.items.filter(menu_id=data["menu_id"], options__isnull=True).first()
    item_quantity = item.quantity if item else 0
    item_quantity = max(0, item_quantity + data["delta"])

    if item is None and item_quantity > 0:
        append_item(
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

    items = cart_items(user)
    return {
        "cart_count": sum(item["quantity"] for item in items),
        "item_quantity": item_quantity,
    }


def update_item_quantity(user, index, quantity):
    items = list(get_or_create_user_cart(user).items.all())
    if 0 <= index < len(items):
        item = items[index]
        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            item.subtotal = item.unit_price * quantity
            item.save(update_fields=["quantity", "subtotal", "updated_at"])
    return _summarize(cart_items(user))


def remove_item(user, index):
    items = list(get_or_create_user_cart(user).items.all())
    if 0 <= index < len(items):
        items[index].delete()
    return _summarize(cart_items(user))


def remove_last_item_by_menu(user, menu_id):
    cart = get_or_create_user_cart(user)
    item = cart.items.filter(menu_id=menu_id).order_by("-sort_order", "-id").first()
    if item:
        item.delete()
    items = cart_items(user)
    return {
        "cart_count": sum(item["quantity"] for item in items),
        "item_quantity": sum(
            item["quantity"] for item in items if item["menu_id"] == menu_id
        ),
    }


def latest_item_snapshot(item):
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

    return _build_cart_item(
        menu.pk,
        menu.name,
        menu.price,
        item["quantity"],
        latest_options,
    ) | {"id": item.get("id")}


def sync_prices(user):
    cart = get_or_create_user_cart(user)
    with transaction.atomic():
        for item in cart.items.select_related("menu").prefetch_related("options__opt"):
            latest = latest_item_snapshot(serialize_cart_item(item))
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


def _db_data_from_cart_item(item):
    return {
        "menu_id": item["menu_id"],
        "name": item["name"],
        "price": item["base_price"],
        "quantity": item["quantity"],
        "options": item.get("options", []),
    }


def _option_price(options):
    return sum(opt.get("price", 0) for opt in options)


def _build_cart_item(menu_id, name, price, quantity, options=None):
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


def _summarize(items):
    return {
        "total": sum(item["subtotal"] for item in items),
        "cart_count": sum(item["quantity"] for item in items),
    }
