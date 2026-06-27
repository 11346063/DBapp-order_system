from django.urls import re_path

from web_app.websockets.customer import CustomerOrderConsumer
from web_app.websockets.staff import StaffConsumer

websocket_urlpatterns = [
    re_path(r"ws/staff/$", StaffConsumer.as_asgi()),
    re_path(r"ws/order/(?P<order_id>\d+)/$", CustomerOrderConsumer.as_asgi()),
]
