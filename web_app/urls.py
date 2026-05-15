from django.contrib.auth import views as auth_views
from django.urls import include, path

from web_app.forms.password_reset_form import (
    AccountPasswordResetForm,
    AccountSetPasswordForm,
)
from web_app.views.auth_views import login_view, logout_view, register_view
from web_app.views.cart import cart_view
from web_app.views.home import assisted_ordering_view, home_view
from web_app.views.order_history import order_history_view
from web_app.views.payment import order_submit, payment_view
from web_app.views.staff import account_management, staff_order_list, staff_report
from web_app.views.type.type_views import typeCreate

app_name = "web_app"

urlpatterns = [
    # 首頁
    path("", home_view, name="home"),
    path("staff/assisted-ordering/", assisted_ordering_view, name="assisted_ordering"),
    # 購物車頁面（HTML）
    path("cart/", cart_view, name="cart"),
    # 結帳
    path("payment/", payment_view, name="payment"),
    path("order/submit/", order_submit, name="order_submit"),
    # 訂單歷史
    path("orders/", order_history_view, name="order_history"),
    # 身份認證
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
    # 員工 / 管理員頁面
    path("staff/orders/", staff_order_list, name="staff_orders"),
    path("staff/report/", staff_report, name="staff_report"),
    path("staff/accounts/", account_management, name="account_management"),
    path("type/create/", typeCreate, name="type_create"),
    # RESTful API（DRF）
    path("api/", include("web_app.api.urls")),
]
