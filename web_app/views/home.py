from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from web_app.models import Type, Identity
from web_app.services import menu as menu_service


@ensure_csrf_cookie
def home_view(request):
    types = Type.objects.all()
    search_query = request.GET.get("q", "").strip()
    user = request.user
    is_staff = user.is_authenticated and user.identity in (
        Identity.ADMIN,
        Identity.EMPLOYEE,
    )
    can_manage_menu = user.is_authenticated and user.identity == Identity.ADMIN
    menus = menu_service.visible_menus_for_user(user, search_query)

    page_urls = {
        "menuToggle": reverse("web_app:menu_toggle", kwargs={"pk": 0}).replace(
            "/0/", "/{id}/"
        ),
        "menuEdit": reverse("web_app:menu_edit", kwargs={"pk": 0}).replace(
            "/0/", "/{id}/"
        ),
        "menuCreate": reverse("web_app:menu_create"),
    }

    return render(
        request,
        "home.html",
        {
            "types": types,
            "menus": menus,
            "search_query": search_query,
            "is_staff": is_staff,
            "can_manage_menu": can_manage_menu,
            "show_customer_ordering": not is_staff,
            "page_urls": page_urls,
        },
    )


@ensure_csrf_cookie
def assisted_ordering_view(request):
    user = request.user
    if not user.is_authenticated or user.identity not in (
        Identity.ADMIN,
        Identity.EMPLOYEE,
    ):
        return redirect("web_app:home")

    types = Type.objects.all()
    search_query = request.GET.get("q", "").strip()
    menus = menu_service.assisted_ordering_menus(search_query)

    return render(
        request,
        "home.html",
        {
            "types": types,
            "menus": menus,
            "search_query": search_query,
            "is_staff": False,
            "can_manage_menu": False,
            "show_customer_ordering": True,
            "is_assisted_ordering": True,
            "page_urls": {},
            "page_title": _("代客點餐"),
        },
    )
