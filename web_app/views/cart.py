from django.shortcuts import render
from django.urls import reverse

from web_app.models import Identity
from web_app.services import cart as cart_service


def _ordering_return_url(request):
    if request.user.is_authenticated and request.user.identity in (
        Identity.ADMIN,
        Identity.EMPLOYEE,
    ):
        return reverse("web_app:assisted_ordering")
    return reverse("web_app:home")


def cart_view(request):
    cart = cart_service.get_cart(request.session)
    total = cart_service.cart_total(cart)
    return render(
        request,
        "cart.html",
        {
            "cart_items": cart,
            "total": total,
            "ordering_return_url": _ordering_return_url(request),
        },
    )
