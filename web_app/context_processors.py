from web_app.enums import Identity
from web_app.services import cart as cart_service


def cart_count(request):
    user = request.user
    if user.is_authenticated and getattr(user, "identity", None) in (
        Identity.ADMIN,
        Identity.EMPLOYEE,
    ):
        return {"cart_count": 0}
    cart = cart_service.get_cart(user, request.session)
    return {"cart_count": cart_service.cart_count(cart)}
