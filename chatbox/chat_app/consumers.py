import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import TypingIndicator, ChatRoom, OnlineUser
from users_app.models import Message, Conversation

User = get_user_model()