def option_price(options):
    return sum(opt.get("price", 0) for opt in options)


def build_cart_item(menu_id, name, price, quantity, options=None):
    options = options or []
    opts_price = option_price(options)
    unit_price = price + opts_price
    return {
        "menu_id": menu_id,
        "name": name,
        "base_price": price,
        "options": options,
        "options_price": opts_price,
        "unit_price": unit_price,
        "quantity": quantity,
        "subtotal": unit_price * quantity,
    }
