from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from web_app.services import cart as cart_service
from web_app.services import order as order_service
from web_app.services.exceptions import EmptyCartError, StaffCustomerPhoneRequired


def payment_view(request):
    cart = cart_service.get_cart(request.session)
    if not cart:
        messages.warning(request, _("購物車是空的"))
        return redirect("web_app:home")

    total = cart_service.cart_total(cart)
    return render(
        request,
        "payment.html",
        {
            "cart_items": cart,
            "total": total,
            "is_guest": not request.user.is_authenticated,
            "is_staff_order": order_service.is_staff_order_user(request.user),
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

    messages.success(request, _("訂單 #{pk} 已成功送出！").format(pk=order.pk))
    return redirect("web_app:home")
