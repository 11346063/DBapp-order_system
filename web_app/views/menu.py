from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from ..models import Menu

# 權限要求：必須有 web_app.change_menu 權限的人才能進入
class StaffRequiredMixin(PermissionRequiredMixin):
    permission_required = 'web_app.change_menu'

# 1. 菜單列表 (所有人登入後可看)
class MenuListView(LoginRequiredMixin, ListView):
    model = Menu
    template_name = 'web_app/templates/menu_list.html'
    context_object_name = 'menus'

# 2. 新增菜單 (需員工權限)
class MenuCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Menu
    fields = ['type', 'name', 'price', 'opt_group', 'info', 'remark']
    template_name = 'web_app/templates/menu_form.html'
    success_url = reverse_lazy('menu_list')

# 3. 修改菜單 (需員工權限)
class MenuUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Menu
    fields = ['type', 'name', 'price', 'opt_group', 'info', 'remark']
    template_name = 'web_app/templates/menu_form.html'
    success_url = reverse_lazy('menu_list')

# 4. 刪除菜單 (需員工權限)
class MenuDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Menu
    template_name = 'web_app/templates/menu_confirm_delete.html'
    success_url = reverse_lazy('menu_list')