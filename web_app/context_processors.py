from web_app.services import cart as cart_service


def cart_count(request):
    cart = cart_service.get_cart(request.user, request.session)
    return {"cart_count": cart_service.cart_count(cart)}
