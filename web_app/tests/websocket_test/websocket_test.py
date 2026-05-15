from channels.generic.websocket import AsyncWebsocketConsumer


class websocket_test(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def connect(self):  # 連線
        await self.accept()

    async def receive(self, text_data=None):  # 回傳處理
        pass

    async def sendLogs(self, data, userId=None):  # 發送
        if not userId:
            userId = self.channel_name
        await self.channel_layer.send(
            userId,
            {
                "type": "chat.message",
                "res": data,
            },
        )

    async def chat_message(self, event):  # 定義發送
        await self.send(text_data=event["res"])
