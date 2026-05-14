from django.urls import path
from django.contrib.auth import views as auth_views
from web_app.views.home import assisted_ordering_view, home_view, menu_detail_api
from web_app.views.auth_views import login_view, register_view, logout_view
from web_app.forms.password_reset_form import (
    AccountPasswordResetForm,
    AccountSetPasswordForm,
)
from web_app.views.cart import (
    cart_view,
    cart_add,
    cart_adjust,
    cart_update,
    cart_remove,
)
from web_app.views.payment import payment_view, order_submit
from web_app.views.staff import (
    account_management,
    staff_order_list,
    staff_update_status,
    staff_report,
)
from web_app.views.order_history import order_history_view, reorder
from web_app.views.request_response import request_response_demo
from web_app.views.type.type_views import typeCreate
from web_app.views.menu_manage import menu_toggle_status, menu_edit, menu_create

app_name = "web_app"

urlpatterns = [
    path("", home_view, name="home"),
    path(
        "staff/assisted-ordering/",
        assisted_ordering_view,
        name="assisted_ordering",
    ),
    path("api/menu/<int:pk>/", menu_detail_api, name="menu_detail_api"),
    path("request-response/", request_response_demo, name="request_response_demo"),
    path("cart/", cart_view, name="cart"),
    path("cart/add/", cart_add, name="cart_add"),
    path("cart/adjust/", cart_adjust, name="cart_adjust"),
    path("cart/update/", cart_update, name="cart_update"),
    path("cart/remove/", cart_remove, name="cart_remove"),
    path("payment/", payment_view, name="payment"),
    path("order/submit/", order_submit, name="order_submit"),
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="auth/password_reset.html",
            email_template_name="auth/password_reset_email.html",
            subject_template_name="auth/password_reset_subject.txt",
            form_class=AccountPasswordResetForm,
            success_url="done/",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="auth/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html",
            form_class=AccountSetPasswordForm,
            success_url="/password-reset/complete/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path("orders/", order_history_view, name="order_history"),
    path("orders/reorder/", reorder, name="reorder"),
    path("staff/orders/", staff_order_list, name="staff_orders"),
    path(
        "staff/orders/<int:pk>/status/", staff_update_status, name="staff_order_status"
    ),
    path("staff/report/", staff_report, name="staff_report"),
    path("staff/accounts/", account_management, name="account_management"),
    path("type/create/", typeCreate, name="type_create"),
    path("api/menu/<int:pk>/toggle/", menu_toggle_status, name="menu_toggle"),
    path("api/menu/<int:pk>/edit/", menu_edit, name="menu_edit"),
    path("api/menu/create/", menu_create, name="menu_create"),
]
