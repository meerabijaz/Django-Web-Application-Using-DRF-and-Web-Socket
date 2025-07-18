# ChatApp/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Message # Make sure your models are imported
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import Profile

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Ensure the user is authenticated before allowing WebSocket connection.
        # self.scope['user'] is populated by AuthMiddlewareStack in asgi.py.
        if not self.scope["user"].is_authenticated:
            await self.close() # Close the connection if the user is not authenticated
            return

        self.room_name = f"room_{self.scope['url_route']['kwargs']['room_name']}"
        room_name_param = self.scope['url_route']['kwargs']['room_name']
        if room_name_param == 'global':
            await self.channel_layer.group_add(f'user_{self.scope["user"].username}', self.channel_name)
        else:
            await self.channel_layer.group_add(self.room_name, self.channel_name)
            await self.channel_layer.group_add(f'user_{self.scope["user"].username}', self.channel_name)
        await self.accept()
        # Set user online
        await self.set_user_online()
        # Mark all received unread messages as read
        if room_name_param != 'global':
            await self.mark_messages_read()
            # Broadcast read event to the room
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'read_event',
                    'username': self.scope['user'].username,
                }
            )
        # Remove user notification group logic

    async def disconnect(self, close_code):
        # Only attempt to discard from group if the user was authenticated and connected
        if self.scope["user"].is_authenticated:
            room_name_param = self.scope['url_route']['kwargs']['room_name']
            if room_name_param == 'global':
                await self.channel_layer.group_discard(f'user_{self.scope["user"].username}', self.channel_name)
            else:
                await self.channel_layer.group_discard(self.room_name, self.channel_name)
                await self.channel_layer.group_discard(f'user_{self.scope["user"].username}', self.channel_name)
            # Remove user notification group logic
            # Set user offline and update last_seen
            await self.set_user_offline()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message')
        room_name = text_data_json.get('room_name')
        sender_username = self.scope['user'].username
        media_url = text_data_json.get('media_url')
        delete_message_id = text_data_json.get('delete_message_id')
        delete_for = text_data_json.get('delete_for')
        typing_status = text_data_json.get('typing')

        if typing_status in ['start', 'stop']:
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'typing_event',
                    'username': sender_username,
                    'status': typing_status,
                }
            )
            # Only return if this is a typing-only event (no message content)
            if not message_content:
                return

        if delete_message_id:
            # Broadcast message deletion
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'delete_message',
                    'message_id': delete_message_id,
                    'delete_for': delete_for,
                    'sender': sender_username,
                }
            )
            return

        if message_content:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'sender': sender_username,
                        'message': message_content,
                        'room_name': room_name,
                        'media_url': media_url,
                    }
                }
            )

    # This method is called when an event with 'type': 'chat_message' is received by the consumer
    async def chat_message(self, event):
        data = event['message'] # This 'message' key contains the dictionary sent from receive()

        # Save the message to the database and get timestamp
        timestamp = await self.create_message(data=data)
        # Update message status to delivered for all except sender
        await self.mark_message_delivered(data)

        # Prepare response data to send back to the WebSocket
        response_data = {
            'sender': data['sender'],
            'message': data['message'],
            'media_url': data.get('media_url'),
            'timestamp': timestamp,
            'status': 'delivered',
        }
        # Send message to the WebSocket
        await self.send(text_data=json.dumps({'message': response_data}))
        # Unread badge notification logic removed

    async def delete_message(self, event):
        # Notify clients to remove the message from UI
        await self.send(text_data=json.dumps({
            'delete_message_id': event['message_id'],
            'delete_for': event['delete_for'],
            'sender': event['sender'],
        }))

    async def typing_event(self, event):
        # Send typing event to all users except the sender
        if self.scope['user'].username != event['username']:
            await self.send(text_data=json.dumps({
              'typing': {
                 'username': event['username'],
                  'status': event['status']
                }
        }))

    async def read_event(self, event):
        # Notify all users in the room that messages have been read by this user
        if self.scope['user'].username != event['username']:
            await self.send(text_data=json.dumps({
                'read': {
                    'username': event['username']
                }
            }))

    async def new_group_event(self, event):
        print(f"[DEBUG] new_group_event received in consumer for user {self.scope['user'].username}: {event['group_info']}")
        await self.send(text_data=json.dumps({
            'new_group': event['group_info']
        }))


    @database_sync_to_async
    def set_user_online(self):
        user = self.scope["user"]
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.is_online = True
        profile.save()

    @database_sync_to_async
    def set_user_offline(self):
        user = self.scope["user"]
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.is_online = False
        profile.last_seen = timezone.now()
        profile.save()

    @database_sync_to_async
    def mark_messages_read(self):
        user = self.scope["user"]
        room_name = self.scope['url_route']['kwargs']['room_name']
        try:
            room = Room.objects.get(room_name=room_name)
            unread_msgs = Message.objects.filter(room=room, status__in=["sent", "delivered"]).exclude(sender=user)
            unread_msgs.update(status="read")
        except Room.DoesNotExist:
            pass

    @database_sync_to_async
    def mark_message_delivered(self, data):
        try:
            room = Room.objects.get(room_name=data['room_name'])
            msg = Message.objects.filter(room=room, sender__username=data['sender'], message=data['message']).order_by('-timestamp').first()
            if msg and msg.status == 'sent':
                msg.status = 'delivered'
                msg.save()
        except Room.DoesNotExist:
            pass

    @database_sync_to_async
    def create_message(self, data):
        try:
            get_room_by_name = Room.objects.get(room_name=data['room_name'])
            sender_user = User.objects.get(username=data['sender'])
            new_message = Message(room=get_room_by_name, sender=sender_user, message=data['message'], status='sent')
            new_message.save()
            return new_message.timestamp.isoformat()  # Always return ISO timestamp
        except Room.DoesNotExist:
            print(f"Room with name {data['room_name']} does not exist.")
        except User.DoesNotExist:
            print(f"User with username {data['sender']} does not exist.")
        except Exception as e:
            print(f"Error saving message: {e}")
            print(f"Room with name {data['room_name']} does not exist.")
        return None
