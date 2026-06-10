import json

from channels.generic.websocket import AsyncWebsocketConsumer


class StaffConsumer(AsyncWebsocketConsumer):
    room_group_name = "staff_logs"

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated or user.identity not in ("A", "E"):
            await self.close()
            return
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None):
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "res": text_data},
        )

    async def order_notification(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_message(self, event):
        await self.send(text_data=event["res"])
