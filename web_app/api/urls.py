from django.urls import path

from web_app.api.views.cart import (
    CartAddAPIView,
    CartAdjustAPIView,
    CartRemoveAPIView,
    CartUpdateAPIView,
)
from web_app.api.views.menu import (
    MenuCreateAPIView,
    MenuDetailAPIView,
    MenuToggleAPIView,
    MenuUpdateAPIView,
)
from web_app.api.views.order import OrderStatusAPIView, ReorderAPIView

urlpatterns = [
    # Menu
    path("menu/<int:pk>/", MenuDetailAPIView.as_view(), name="menu_detail_api"),
    path("menu/<int:pk>/toggle/", MenuToggleAPIView.as_view(), name="menu_toggle"),
    path("menu/<int:pk>/edit/", MenuUpdateAPIView.as_view(), name="menu_edit"),
    path("menu/create/", MenuCreateAPIView.as_view(), name="menu_create"),
    # Cart
    path("cart/add/", CartAddAPIView.as_view(), name="cart_add_api"),
    path("cart/adjust/", CartAdjustAPIView.as_view(), name="cart_adjust_api"),
    path("cart/update/", CartUpdateAPIView.as_view(), name="cart_update_api"),
    path("cart/remove/", CartRemoveAPIView.as_view(), name="cart_remove_api"),
    # Orders
    path(
        "orders/<int:pk>/status/", OrderStatusAPIView.as_view(), name="api_order_status"
    ),
    path("orders/reorder/", ReorderAPIView.as_view(), name="api_reorder"),
]
