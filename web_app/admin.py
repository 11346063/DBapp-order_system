from django.contrib import admin
from django.utils.timezone import now
from .models.order import Order
from .models.order_item import OrderItem
from .models.user import User
from .models.menu import Menu
from .models.type import Type
from .models.options import Options
from .models.opt_group import OptGroup


# --- 1. Inline 設定：讓你在訂單頁面直接編輯品項與選項 ---

# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     extra = 0  # 預設不額外顯示空白列
#     readonly_fields = ('total_price',) # 總價通常由系統計算

# class OrderItemOptionsInline(admin.TabularInline):
#     model = OrderItemOptions
#     extra = 0

# --- 2. Order 客製化：核心 CRUD 介面 ---

# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     # A. 列表欄位與搜尋
#     list_display = ('sno', 'get_user_name', 'price_total', 'status_label', 'create_time')
#     list_filter = ('status', 'create_time')
#     search_fields = ('sno', 'user__name', 'user__phone_number')
#     ordering = ('-create_time',)
    
#     # 將關聯模型內聯進訂單編輯頁面
#     # inlines = [OrderItemInline, OrderItemOptionsInline]

#     # B. 表單欄位分組 (Fieldsets)
#     fieldsets = (
#         ('訂單識別', {
#             'fields': ('sno', 'user', 'status')
#         }),
#         ('金額資訊', {
#             'fields': ('price_total',),
#         }),
#         ('時間紀錄', {
#             'fields': ('create_time',),
#             'classes': ('collapse',), # 可折疊
#         }),
#     )

#     # C. 衍生欄位 (Computed Fields)
#     @admin.display(description='客戶名稱')
#     def get_user_name(self, obj):
#         return obj.user.name

#     @admin.display(description='訂單狀態')
#     def status_label(self, obj):
#         # 假設 1: 處理中, 2: 已完成, 0: 已取消
#         status_mapping = {1: "⏳ 處理中", 2: "✅ 已完成", 0: "❌ 已取消"}
#         return status_mapping.get(obj.status, "❓ 未知")

#     # D. Actions 批次處理
#     actions = ['mark_as_completed']

    # @admin.action(description='將選取訂單標記為「已完成」')
    # def mark_as_completed(self, request, queryset):
    #     updated_count = queryset.update(status=2)
    #     self.message_user(request, f'成功更新 {updated_count} 筆訂單為已完成狀態。')

    # # E. 自動觸發程序 (save_model)
    # def save_model(self, request, obj, form, change):
    #     """
    #     當在 Admin 後台存檔時觸發
    #     """
    #     if not change: # 只有在「新增」時自動給予編號或預設時間
    #         if not obj.create_time:
    #             obj.create_time = now()
        
    #     # 這裡可以寫入業務邏輯，例如檢查庫存或計算總金額
    #     super().save_model(request, obj, form, change)

# --- 3. 其他模型的客製化 ---

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'price', 'remark')
    list_editable = ('price',) # 可以在列表頁直接改價格
    search_fields = ('name',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'phone_number', 'status', 'update_time')
    list_filter = ('status',)
    # 隱藏密碼，或僅以唯讀顯示
    exclude = ('password',) 
    readonly_fields = ('create_time', 'update_time')

# 註冊其餘基礎模型
admin.site.register(Type)
admin.site.register(Options)
admin.site.register(OptGroup)