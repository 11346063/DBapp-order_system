from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.translation import gettext as _
from web_app.forms.login_form import LoginForm
from web_app.forms.register_form import RegisterForm
from web_app.models import Identity
from web_app.services import cart as cart_service


def login_view(request):
    if request.user.is_authenticated:
        return redirect("web_app:home")

    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            account = form.cleaned_data["account"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=account, password=password)
            if user is not None:
                login(request, user)
                cart_service.merge_session_cart_to_db(user, request.session)
                messages.success(
                    request, _("歡迎回來，{name}！").format(name=user.name)
                )
                if user.identity in (Identity.ADMIN, Identity.EMPLOYEE):
                    return redirect("web_app:staff_orders")
                next_url = request.GET.get("next", "web_app:home")
                return redirect(next_url)
            else:
                messages.error(request, _("手機號碼或密碼錯誤"))

    return render(request, "auth/login.html", {"form": form})


def register_view(request):
    # 注意：RegisterForm 含 captcha 欄位，render 時會觸發同步 DB 寫入，
    # 因此本 view 保持同步（async view 會造成 SynchronousOnlyOperation）
    if request.user.is_authenticated:
        return redirect("web_app:home")

    form = RegisterForm()
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.identity = Identity.CUSTOMER
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, _("註冊成功！請登入"))
            return redirect("web_app:login")

    return render(request, "auth/register.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, _("已成功登出"))
    return redirect("web_app:home")
