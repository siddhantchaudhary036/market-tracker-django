import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import TaskControl
from asgiref.sync import sync_to_async
from .tasks import fetch_ltp
import asyncio

class NewsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"news_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        ticker = self.room_name
        print('CONNECTED', ticker)
        await sync_to_async(TaskControl.objects.update_or_create)(ticker=ticker, defaults={'should_run': True})

        await self.accept()

        # Calling the ltp updation task upon WS connection
        asyncio.create_task(fetch_ltp(ticker))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        ticker = self.room_name
        print('DISCONNECTED', ticker)
        await sync_to_async(TaskControl.objects.update_or_create)(ticker=ticker, defaults={'should_run': False})

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "ltp_update", "message": message}
        )

    # Receive message from room group1

    async def ltp_update(self, event):
        ltp_value = event['ltp_value']
        print('received ltp update', ltp_value, self.room_name)

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"ltp_value": ltp_value}))
