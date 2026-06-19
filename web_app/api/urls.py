from django.urls import path

from web_app.api.views.cart import (
    CartAddAPIView,
    CartAdjustAPIView,
    CartDetailAPIView,
    CartRemoveAPIView,
    CartRemoveByMenuAPIView,
    CartSyncPricesAPIView,
    CartUpdateAPIView,
    CartValidatePricesAPIView,
)
from web_app.api.views.menu import (
    MenuCreateAPIView,
    MenuDetailAPIView,
    MenuSoldOutTodayAPIView,
    MenuToggleAPIView,
    MenuUpdateAPIView,
)
from web_app.api.views.order import (
    CustomerCancelOrderAPIView,
    OrderAcceptAPIView,
    OrderCustomerStatusAPIView,
    OrderReadyAPIView,
    OrderStatusAPIView,
    ReorderAPIView,
    StaffOrderCreateAPIView,
)
from web_app.api.views.print import (
    OrderReprintAPIView,
    PrintAckAPIView,
    PrintPendingAPIView,
)

urlpatterns = [
    # Menu
    path("menu/<int:pk>/", MenuDetailAPIView.as_view(), name="menu_detail_api"),
    path("menu/<int:pk>/toggle/", MenuToggleAPIView.as_view(), name="menu_toggle"),
    path("menu/<int:pk>/edit/", MenuUpdateAPIView.as_view(), name="menu_edit"),
    path(
        "menu/<int:pk>/sold-out-today/",
        MenuSoldOutTodayAPIView.as_view(),
        name="menu_sold_out_today",
    ),
    path("menu/create/", MenuCreateAPIView.as_view(), name="menu_create"),
    # Cart
    path("cart/", CartDetailAPIView.as_view(), name="cart_detail_api"),
    path("cart/add/", CartAddAPIView.as_view(), name="cart_add_api"),
    # adjust: 菜單頁用，以 menu_id 定位、delta 相對增減（不含選項品項）
    path("cart/adjust/", CartAdjustAPIView.as_view(), name="cart_adjust_api"),
    # update: 購物車頁用，以陣列 index 定位、直接設定絕對數量
    path("cart/update/", CartUpdateAPIView.as_view(), name="cart_update_api"),
    path("cart/remove/", CartRemoveAPIView.as_view(), name="cart_remove_api"),
    path(
        "cart/remove-by-menu/",
        CartRemoveByMenuAPIView.as_view(),
        name="cart_remove_by_menu_api",
    ),
    path(
        "cart/validate-prices/",
        CartValidatePricesAPIView.as_view(),
        name="cart_validate_prices_api",
    ),
    path(
        "cart/sync-prices/",
        CartSyncPricesAPIView.as_view(),
        name="cart_sync_prices_api",
    ),
    # Cart v1 aliases
    path("v1/cart/", CartDetailAPIView.as_view(), name="v1_cart_detail_api"),
    path(
        "v1/cart/validate-prices/",
        CartValidatePricesAPIView.as_view(),
        name="v1_cart_validate_prices_api",
    ),
    path(
        "v1/cart/sync-prices/",
        CartSyncPricesAPIView.as_view(),
        name="v1_cart_sync_prices_api",
    ),
    # Orders
    path(
        "orders/<int:pk>/status/", OrderStatusAPIView.as_view(), name="api_order_status"
    ),
    path("orders/<int:pk>/ready/", OrderReadyAPIView.as_view(), name="api_order_ready"),
    path(
        "orders/<int:pk>/accept/", OrderAcceptAPIView.as_view(), name="api_order_accept"
    ),
    path("orders/reorder/", ReorderAPIView.as_view(), name="api_reorder"),
    path(
        "orders/<int:pk>/customer-status/",
        OrderCustomerStatusAPIView.as_view(),
        name="api_order_customer_status",
    ),
    path(
        "orders/<int:pk>/customer-cancel/",
        CustomerCancelOrderAPIView.as_view(),
        name="api_order_customer_cancel",
    ),
    path(
        "orders/<int:pk>/reprint/",
        OrderReprintAPIView.as_view(),
        name="api_order_reprint",
    ),
    # Staff assisted ordering (direct, no cart)
    path(
        "v1/orders/staff/",
        StaffOrderCreateAPIView.as_view(),
        name="v1_staff_order_create",
    ),
    # 出單機列印代理
    path("print/pending/", PrintPendingAPIView.as_view(), name="api_print_pending"),
    path("print/<int:pk>/ack/", PrintAckAPIView.as_view(), name="api_print_ack"),
]
