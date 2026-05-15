from django.shortcuts import redirect, render
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.translation import gettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from web_app.models import Menu, Type, Identity


MENU_PAGE_SIZE = 12


def _search_menus(queryset, query):
    if not query:
        return queryset
    return queryset.filter(
        Q(name__icontains=query)
        | Q(info__icontains=query)
        | Q(remark__icontains=query)
        | Q(type__type_name__icontains=query)
    )


def _paginate_menus(request, queryset):
    paginator = Paginator(queryset.order_by("type__type_name", "name"), MENU_PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))
    return paginator, page_obj


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
    if is_staff:
        menus = Menu.objects.select_related("type").all()
    else:
        menus = Menu.objects.select_related("type").filter(status=True)
    menus = _search_menus(menus, search_query)
    paginator, page_obj = _paginate_menus(request, menus)

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
            "menus": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
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
    menus = Menu.objects.select_related("type").filter(status=True)
    menus = _search_menus(menus, search_query)
    paginator, page_obj = _paginate_menus(request, menus)

    return render(
        request,
        "home.html",
        {
            "types": types,
            "menus": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
            "search_query": search_query,
            "is_staff": False,
            "can_manage_menu": False,
            "show_customer_ordering": True,
            "is_assisted_ordering": True,
            "page_urls": {},
            "page_title": _("代客點餐"),
        },
    )
