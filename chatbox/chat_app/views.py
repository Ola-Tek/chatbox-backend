from django.shortcuts import render
from .serializers import *
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import *
from django.utils import timezone
from rest_framework import viewsets, permissions, status

# Create your views here.
class ChatRoomViewSet(viewsets.ModelViewSet):
    """the viewset that manages chatroom"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatRoomSerializer
    queryset = ChatRoom.objects.all()
    
    def get_queryset(self):
        """get all active chatrooms"""
        return ChatRoom.objects.filter(is_active=True)
    
    @action(detail=True, methods='post')
    def join_chatroom(self, request, pk=None):
        """joining a chatroom"""
        chat_room = self.get_object
        user = request.user
        
        online_user, created = OnlineUser.objects.update_or_create(
            user=user,
            defaults={
                'current_room': chat_room,
                'last_activity': timezone.now()
            }
        )
        
