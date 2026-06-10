from django.urls import re_path
from web_app.tests.websocket_test import consumers
from web_app.websockets.staff import StaffConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/logs/$", consumers.LogConsumer.as_asgi()),
    re_path(r"ws/staff/$", StaffConsumer.as_asgi()),
]
