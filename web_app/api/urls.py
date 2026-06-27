from django.urls import path

from web_app.api.views.cart import (
    CartSyncPricesAPIView,
    CartValidatePricesAPIView,
)
from web_app.api.views.menu import (
    MenuCreateAPIView,
    MenuDetailAPIView,
    MenuSoldOutTodayAPIView,
    MenuToggleAPIView,
    MenuUpdateAPIView,
)
from web_app.api.views.options import OptionUpdateAPIView
from web_app.api.views.order import (
    CustomerCancelOrderAPIView,
    OrderAcceptAPIView,
    OrderCustomerStatusAPIView,
    OrderReadyAPIView,
    OrderStatusAPIView,
    ReorderAPIView,
    StaffOrderCreateAPIView,
)
from web_app.api.views.preferences import TimezonePreferenceAPIView
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
    # Options
    path("options/<int:pk>/", OptionUpdateAPIView.as_view(), name="api_option_update"),
    # Cart — validate & sync only (CRUD 由前端 localStorage 處理)
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
    # Preferences
    path(
        "v1/preferences/timezone/",
        TimezonePreferenceAPIView.as_view(),
        name="v1_preferences_timezone",
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
