from web_app.services._cart_utils import build_cart_item, option_price
from web_app.services.exceptions import NotFoundError, PriceChangedError


def cart_count(cart):
    return sum(item["quantity"] for item in cart)


def cart_total(cart):
    return sum(item["subtotal"] for item in cart)


def summarize_cart(cart):
    return {"total": cart_total(cart), "cart_count": cart_count(cart)}


def _coerce_cart_item(item):
    options = item.get("options", [])
    base_price = item.get("base_price", item.get("price", 0))
    opts_price = item.get("options_price", option_price(options))
    unit_price = item.get("unit_price", base_price + opts_price)
    quantity = item.get("quantity", 1)
    return {
        "menu_id": item.get("menu_id"),
        "name": item.get("name", ""),
        "base_price": base_price,
        "options": options,
        "options_price": opts_price,
        "unit_price": unit_price,
        "quantity": quantity,
        "subtotal": item.get("subtotal", unit_price * quantity),
    }


def validate_prices_for_cart(cart_items):
    """批量驗證購物車品項價格是否與目前 DB 相符（2 次 DB 查詢）。"""
    if not cart_items:
        return {
            "has_changes": False,
            "old_total": 0,
            "new_total": 0,
            "price_changes": [],
        }

    snapshots = _batch_latest_snapshots(cart_items)
    old_total = cart_total(cart_items)
    new_total = 0
    price_changes = []

    for index, (item, latest) in enumerate(zip(cart_items, snapshots)):
        new_total += latest["subtotal"]
        if _has_price_change(item, latest):
            price_changes.append(
                {
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


def sync_prices_for_cart(cart_items):
    """將購物車品項更新為最新價格，回傳更新後的 cart list（不寫 DB/session）。"""
    if not cart_items:
        return []
    return _batch_latest_snapshots(cart_items)


def ensure_prices_current(cart):
    result = validate_prices_for_cart(cart)
    if result["has_changes"]:
        raise PriceChangedError("部分餐點價格已更新，請確認最新價格後再送出")


def _batch_latest_snapshots(items):
    from web_app.models import Menu, Options

    menu_ids = [item["menu_id"] for item in items]
    menus = {m.pk: m for m in Menu.objects.filter(pk__in=menu_ids)}

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

        latest_opts = []
        for opt_data in item.get("options", []):
            opt_id = opt_data.get("id")
            if not opt_id:
                continue
            opt = options.get(opt_id)
            if opt is None:
                raise NotFoundError("找不到此選項")
            latest_opts.append(
                {
                    "id": opt.pk,
                    "name": opt.name,
                    "price": opt.price,
                    "level": int(opt_data.get("level", 1)),
                }
            )

        snapshots.append(
            build_cart_item(
                menu.pk, menu.name, menu.price, item["quantity"], latest_opts
            )
        )

    return snapshots


def _has_price_change(item, latest):
    return (
        item["base_price"] != latest["base_price"]
        or item["options_price"] != latest["options_price"]
        or item["unit_price"] != latest["unit_price"]
        or item["subtotal"] != latest["subtotal"]
        or item.get("options", []) != latest.get("options", [])
    )
