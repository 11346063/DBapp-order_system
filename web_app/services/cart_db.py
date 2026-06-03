from django.db import transaction
from django.db.models import Max

from web_app.models import Cart, CartItem, CartItemOption, Identity, Menu, Options
from web_app.services._cart_utils import build_cart_item, option_price
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
    opts_price = option_price(options)
    unit_price = base_price + opts_price
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
            options_price=opts_price,
            unit_price=unit_price,
            subtotal=unit_price * quantity,
            sort_order=next_order,
        )
        for opt in options:
            CartItemOption.objects.create(
                cart_item=cart_item,
                opt_id=opt["id"],
                name=opt["name"],
                price=opt["price"],
                level=opt.get("level", 1),
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
        "cart_count": _summarize(items)["cart_count"],
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
        "cart_count": _summarize(items)["cart_count"],
        "item_quantity": sum(i["quantity"] for i in items if i["menu_id"] == menu_id),
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

    return build_cart_item(
        menu.pk,
        menu.name,
        menu.price,
        item["quantity"],
        latest_options,
    ) | {"id": item.get("id")}


def batch_latest_snapshots(items):
    """批量取得多個品項的最新快照，只需 2 次 DB 查詢（取代 N × (1+M) 次）。"""
    if not items:
        return []

    # 1 次查詢取得所有 Menu
    menu_ids = [item["menu_id"] for item in items]
    menus = {m.pk: m for m in Menu.objects.filter(pk__in=menu_ids)}

    # 1 次查詢取得所有 Options
    all_opt_ids = [
        opt["id"] for item in items for opt in item.get("options", []) if opt.get("id")
    ]
    options = (
        {o.pk: o for o in Options.objects.filter(pk__in=all_opt_ids)}
        if all_opt_ids
        else {}
    )

    snapshots = []
    for item in items:
        menu = menus.get(item["menu_id"])
        if menu is None:
            raise NotFoundError("找不到此餐點")

        latest_options = []
        for option in item.get("options", []):
            opt_id = option.get("id")
            if not opt_id:
                continue
            opt = options.get(opt_id)
            if opt is None:
                raise NotFoundError("找不到此選項")
            latest_options.append(
                {
                    "id": opt.pk,
                    "name": opt.name,
                    "price": opt.price,
                    "level": int(option.get("level", 1)),
                }
            )

        snapshots.append(
            build_cart_item(
                menu.pk,
                menu.name,
                menu.price,
                item["quantity"],
                latest_options,
            )
            | {"id": item.get("id")}
        )

    return snapshots


def sync_prices(user):
    cart = get_or_create_user_cart(user)
    with transaction.atomic():
        for item in cart.items.select_related("menu").prefetch_related("options__opt"):
            # Use already-prefetched menu and options — no extra queries needed
            menu = item.menu
            cart_opts = list(item.options.all())

            new_opts_price = sum(co.opt.price for co in cart_opts)
            new_unit_price = menu.price + new_opts_price
            item.base_price = menu.price
            item.options_price = new_opts_price
            item.unit_price = new_unit_price
            item.subtotal = new_unit_price * item.quantity
            item.save(
                update_fields=[
                    "base_price",
                    "options_price",
                    "unit_price",
                    "subtotal",
                    "updated_at",
                ]
            )

            for co in cart_opts:
                db_opt = co.opt
                if co.name != db_opt.name or co.price != db_opt.price:
                    co.name = db_opt.name
                    co.price = db_opt.price
                    co.save(update_fields=["name", "price"])


def _db_data_from_cart_item(item):
    return {
        "menu_id": item["menu_id"],
        "name": item["name"],
        "price": item["base_price"],
        "quantity": item["quantity"],
        "options": item.get("options", []),
    }


def _summarize(items):
    return {
        "total": sum(item["subtotal"] for item in items),
        "cart_count": sum(item["quantity"] for item in items),
    }
