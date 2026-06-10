import json
from channels.generic.websocket import AsyncWebsocketConsumer

class staff(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = "staff_logs"

    async def connect(self): # 連線
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code): # 斷線
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None):  # 接收資料
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "res": text_data,
            },
        )

    async def sendLogs(self, data, userId=None):
        if not userId:
            userId = self.channel_name
        await self.channel_layer.send(
            userId,
            {
                "type": "chat.message",
                "res": data,
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=event["res"])