from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def employee_required(view_func):
    """限制只有員工（B）或管理員（A）可以訪問"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('web_app:login')
        if request.user.identity not in ('A', 'B'):
            messages.error(request, '權限不足')
            return redirect('web_app:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """限制只有管理員（A）可以訪問"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('web_app:login')
        if request.user.identity != 'A':
            messages.error(request, '權限不足，此頁面僅限管理員')
            return redirect('web_app:staff_orders')
        return view_func(request, *args, **kwargs)
    return wrapper
