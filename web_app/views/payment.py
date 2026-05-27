from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from web_app.models.order import Order
from web_app.services import cart as cart_service
from web_app.services import order as order_service
from web_app.services import store_settings as settings_service
from web_app.services.exceptions import (
    CheckoutPhoneRequired,
    EmptyCartError,
    PriceChangedError,
    StaffCustomerPhoneRequired,
    ValidationServiceError,
)


def payment_view(request):
    cart = cart_service.get_cart(request.user, request.session)
    if not cart:
        messages.warning(request, _("購物車是空的"))
        return redirect("web_app:home")

    total = cart_service.cart_total(cart)
    is_staff_order = order_service.is_staff_order_user(request.user)
    checkout_phone_default = ""
    if request.user.is_authenticated and not is_staff_order:
        checkout_phone_default = request.user.phone_number or ""
    custom_options = settings_service.get_active_custom_options()
    s = settings_service.get_settings()
    return render(
        request,
        "payment.html",
        {
            "cart_items": cart,
            "total": total,
            "is_guest": not request.user.is_authenticated,
            "is_staff_order": is_staff_order,
            "checkout_phone_default": checkout_phone_default,
            "custom_options": custom_options,
            "extra_ingredient_cost": s.extra_ingredient_cost,
        },
    )


def order_submit(request):
    if request.method != "POST":
        return redirect("web_app:payment")

    try:
        order = order_service.create_order_from_cart(
            request.user,
            request.session,
            request.POST,
        )
    except EmptyCartError:
        messages.warning(request, _("購物車是空的"))
        return redirect("web_app:home")
    except StaffCustomerPhoneRequired:
        messages.error(request, _("員工代客點餐需要填寫電話"))
        return redirect("web_app:payment")
    except CheckoutPhoneRequired:
        messages.error(request, _("結帳需要填寫聯絡電話"))
        return redirect("web_app:payment")
    except ValidationServiceError as exc:
        messages.error(request, exc.message)
        return redirect("web_app:payment")
    except PriceChangedError:
        messages.warning(request, _("部分餐點價格已更新，請確認最新價格後再送出"))
        return redirect("web_app:payment")

    if order_service.is_staff_order_user(request.user):
        messages.success(request, _("代客訂單已送出，已自動接單"))
        return redirect("web_app:home")

    request.session["last_order_id"] = order.pk
    return redirect("web_app:order_waiting", pk=order.pk)


def order_waiting_view(request, pk):
    try:
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        return redirect("web_app:home")

    if request.user.is_authenticated:
        if order.user_id != request.user.pk:
            return redirect("web_app:home")
    else:
        if request.session.get("last_order_id") != pk:
            return redirect("web_app:home")

    return render(request, "order_waiting.html", {"order_id": pk})
