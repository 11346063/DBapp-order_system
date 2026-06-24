from django.shortcuts import render
from django.urls import reverse

from web_app.models import Identity


def _ordering_return_url(request):
    if request.user.is_authenticated and request.user.identity in (
        Identity.ADMIN,
        Identity.EMPLOYEE,
    ):
        return reverse("web_app:assisted_ordering")
    return reverse("web_app:home")


def cart_view(request):
    return render(
        request,
        "cart.html",
        {"ordering_return_url": _ordering_return_url(request)},
    )
