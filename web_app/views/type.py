# from django.urls import reverse_lazy
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.views.generic import ListView, CreateView, UpdateView, DeleteView
# from ..models import Type

# # 1. 列表檢視：僅限登入使用者
# class TypeListView(LoginRequiredMixin, ListView):
#     model = Type
#     template_name = 'web_app/templates/type_list.html'
#     context_object_name = 'types'
#     # 若未登入，預設會跳轉至 settings.LOGIN_URL

# # 2. 新增類型：僅限登入使用者
# class TypeCreateView(LoginRequiredMixin, CreateView):
#     model = Type
#     fields = ['type_name']
#     template_name = 'web_app/templates/type_form.html'
#     success_url = reverse_lazy('type_list')

# # 3. 修改類型：僅限登入使用者
# class TypeUpdateView(LoginRequiredMixin, UpdateView):
#     model = Type
#     fields = ['type_name']
#     template_name = 'web_app/templates/type_form.html'
#     success_url = reverse_lazy('type_list')

# # 4. 刪除類型：要求「刪除權限」(更嚴格)
# class TypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
#     model = Type
#     permission_required = 'web_app.delete_type' # 權限格式：app名稱.動作_model名稱
#     template_name = 'web_app/templates/type_confirm_delete.html'
#     success_url = reverse_lazy('type_list')