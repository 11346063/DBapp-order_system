def cart_count(request):
    cart = request.session.get("cart", [])
    return {"cart_count": sum(item.get("quantity", 1) for item in cart)}
