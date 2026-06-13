import json

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from web_app.models import Identity, Menu, Options, Type
from web_app.services import menu as menu_service
from web_app.services import store_settings as settings_service


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
        "menuSoldOutToday": reverse(
            "web_app:menu_sold_out_today", kwargs={"pk": 0}
        ).replace("/0/", "/{id}/"),
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

    s = settings_service.get_settings()
    custom_options = settings_service.get_active_custom_options()

    cut_option = Options.objects.filter(name=s.option_name_cut).first()
    cut_required_ids = (
        set(
            Menu.objects.filter(status=True, options=cut_option).values_list(
                "id", flat=True
            )
        )
        if cut_option
        else set()
    )

    return render(
        request,
        "assisted_ordering.html",
        {
            "types": types,
            "menus": menus,
            "search_query": search_query,
            "custom_options": custom_options,
            "extra_ingredient_cost": s.extra_ingredient_cost,
            "cut_required_ids": cut_required_ids,
            "cut_required_ids_json": json.dumps(list(cut_required_ids)),
        },
    )
