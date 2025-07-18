from django.urls import path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    path('ws/notification/<str:room_name>/', ChatConsumer.as_asgi()),
    path('ws/notification/global/', ChatConsumer.as_asgi()),  # Global notification socket
]