from django.shortcuts import render
from .serializers import *
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import *
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from datetime import timedelta, timezone

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
        return Response({
            'message': f"joined {chat_room.name} successfully!",
            'chat room': ChatRoomSerializer(chat_room).data,
            'created': created
        })
    
    @action(detail=True, methods=['post'])    
    def leave_chatroom(self, request, pk=None):
        """on how to leave the chatroom"""
        user = request.user
        chat_room = self.get_object()
        
        try: 
            requested_user = OnlineUser.objects.get(user=user, current_room=chat_room)
            requested_user.current_room == None
            requested_user.save()
            
            return Response ({'message': f'{user} has sucessfully left the group'})
        except requested_user.DoesNotExist:
            return Response({
                'message': 'You are not in this room'
            }, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=True, methods=['get'])
    def online_user(self, request, pk=None):
        """get the total number of online users in a chat room"""
        chat_room = self.get_object()
        
        online_user = OnlineUser.objects.filter(current_room=chat_room)
        serializer = OnlineUserSerializer(online_user, many=True)
        return Response({
            serializer.data()
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])    
    def active_rooms(self, request):
        """get rooms where a current user is active"""
        user = request.user
        rooms = ChatRoom.objects.filter(user=user, is_active=True)
        
        if rooms.exists(): 
            serializer = ChatRoomSerializer(rooms, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
    
        return Response({'message':'You are not active in any room'}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def my_room(self, request):
        """get the room where an active user is"""
        user = request.user
        online_user = OnlineUser.objects.get(user=user)
        
        try:
            
            if online_user.current_room:
                room_serializer = ChatRoomSerializer(online_user.current_room)
                return Response (room_serializer.data)
            else:
                return Response({'message': 'Not in my room!'})
            
        except online_user.DoesNotExist:
            return Response ({'message': 'the user is not onine in this room'})
        
class OnlineUserViewSet(viewsets.ModelViewSet):
    """the viewset that manages online users"""
    queryset = OnlineUser.objects.all()
    serializer_class = OnlineUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    
    def get_queryset(self):
        """get the query set of all online users"""
        return OnlineUser.objects.filter(last_activity__gte=timezone.now() - timedelta(minutes=5))
    
    @action(detail=False, methods=['post'])
    def update_activity(self, request):
        """update the queryset"""
        
        
