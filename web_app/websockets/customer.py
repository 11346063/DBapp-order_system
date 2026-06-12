import json

from channels.generic.websocket import AsyncWebsocketConsumer

from web_app.models import Order


class CustomerOrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.group_name = f"order_{self.order_id}"

        if not await self._is_authorized():
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None):
        pass  # 顧客只監聽，不傳送

    async def order_status_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def _is_authorized(self) -> bool:
        try:
            order = await Order.objects.aget(pk=self.order_id)
        except Order.DoesNotExist:
            return False
        user = self.scope.get("user")
        if user and user.is_authenticated:
            return order.user_id == user.pk
        session = self.scope.get("session", {})
        return session.get("last_order_id") == int(self.order_id)
