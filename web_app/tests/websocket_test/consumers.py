import json,asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "chat_broadcast"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        print(f"收到訊息：{message}")  # ✅ debug 用

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
            }
        )

    async def chat_message(self, event):
        print("✅ 廣播觸發")  # ✅ debug 用
        await self.send(text_data=json.dumps({
            "message": event["message"]
        }))

class LogConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        await self.accept()
        self.is_active = True
        asyncio.create_task(self.send_logs_periodically())

    async def disconnect(self, close_code):
        self.is_active = False

    async def send_logs_periodically(self):
        while self.is_active:
            # logs = get_logs_data()  # ← 回傳為 list 或 dict 都可以
            await self.send(text_data=json.dumps({
                "msg":"successful"
            }))
            # await asyncio.sleep(2)
