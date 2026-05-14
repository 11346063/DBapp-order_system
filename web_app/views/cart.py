import json
from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST


def _ordering_return_url(request):
    if request.user.is_authenticated and request.user.identity in ("A", "E"):
        return reverse("web_app:assisted_ordering")
    return reverse("web_app:home")


def cart_view(request):
    cart = request.session.get("cart", [])
    total = sum(item["subtotal"] for item in cart)
    return render(
        request,
        "cart.html",
        {
            "cart_items": cart,
            "total": total,
            "ordering_return_url": _ordering_return_url(request),
        },
    )


@require_POST
def cart_add(request):
    data = json.loads(request.body)
    cart = request.session.get("cart", [])

    menu_id = data["menu_id"]
    name = data["name"]
    price = data["price"]
    quantity = data.get("quantity", 1)
    options = data.get("options", [])

    options_price = sum(opt["price"] for opt in options)
    unit_price = price + options_price
    subtotal = unit_price * quantity

    cart.append(
        {
            "menu_id": menu_id,
            "name": name,
            "base_price": price,
            "options": options,
            "options_price": options_price,
            "unit_price": unit_price,
            "quantity": quantity,
            "subtotal": subtotal,
        }
    )

    request.session["cart"] = cart
    cart_count = sum(item["quantity"] for item in cart)

    return JsonResponse({"success": True, "cart_count": cart_count})


@require_POST
def cart_adjust(request):
    data = json.loads(request.body)
    cart = request.session.get("cart", [])

    menu_id = data["menu_id"]
    name = data["name"]
    price = data["price"]
    delta = data["delta"]
    item_quantity = 0
    target_index = None

    for index, item in enumerate(cart):
        if item.get("menu_id") == menu_id and item.get("options", []) == []:
            target_index = index
            item_quantity = item["quantity"]
            break

    item_quantity = max(0, item_quantity + delta)

    if target_index is None and item_quantity > 0:
        cart.append(
            {
                "menu_id": menu_id,
                "name": name,
                "base_price": price,
                "options": [],
                "options_price": 0,
                "unit_price": price,
                "quantity": item_quantity,
                "subtotal": price * item_quantity,
            }
        )
    elif target_index is not None and item_quantity <= 0:
        cart.pop(target_index)
    elif target_index is not None:
        cart[target_index]["quantity"] = item_quantity
        cart[target_index]["subtotal"] = cart[target_index]["unit_price"] * item_quantity

    request.session["cart"] = cart
    cart_count = sum(item["quantity"] for item in cart)

    return JsonResponse(
        {"success": True, "cart_count": cart_count, "item_quantity": item_quantity}
    )


@require_POST
def cart_update(request):
    data = json.loads(request.body)
    index = data["index"]
    quantity = data["quantity"]
    cart = request.session.get("cart", [])

    if 0 <= index < len(cart):
        if quantity <= 0:
            cart.pop(index)
        else:
            cart[index]["quantity"] = quantity
            cart[index]["subtotal"] = cart[index]["unit_price"] * quantity

    request.session["cart"] = cart
    total = sum(item["subtotal"] for item in cart)
    cart_count = sum(item["quantity"] for item in cart)

    return JsonResponse({"success": True, "total": total, "cart_count": cart_count})


@require_POST
def cart_remove(request):
    data = json.loads(request.body)
    index = data["index"]
    cart = request.session.get("cart", [])

    if 0 <= index < len(cart):
        cart.pop(index)

    request.session["cart"] = cart
    total = sum(item["subtotal"] for item in cart)
    cart_count = sum(item["quantity"] for item in cart)

    return JsonResponse({"success": True, "total": total, "cart_count": cart_count})
