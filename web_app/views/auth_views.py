from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from web_app.forms.login_form import LoginForm
from web_app.forms.register_form import RegisterForm


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
                messages.success(request, f"歡迎回來，{user.name}！")
                if user.identity == "A" or user.identity == "E":
                    return redirect("web_app:staff_orders")
                next_url = request.GET.get("next", "web_app:home")
                return redirect(next_url)
            else:
                messages.error(request, "帳號或密碼錯誤")

    return render(request, "auth/login.html", {"form": form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("web_app:home")

    form = RegisterForm()
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.identity = "C"
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, "註冊成功！請登入")
            return redirect("web_app:login")

    return render(request, "auth/register.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "已成功登出")
    return redirect("web_app:home")
