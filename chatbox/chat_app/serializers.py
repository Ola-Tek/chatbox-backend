from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model

User = get_user_model()
#rules of serializer:
#1. do not query database in a serializer class
#2. serializer represent information you want to represent in
#serializers define the structure of an output
class ChatRoomSerializer(serializers.ModelSerializer):
    """The serializer after a chat room model""" 
    get_online_users_count = serializers.SerializerMethodField()
    
    class Meta:
        """it tells django which model to move with"""
        model = ChatRoom
        fields = ['name', 'conversation', 'created_at', 'is_active']
        read_only_fields = ['created_at', 'is_active']
        
    def get_online_users_count(self, obj):
        """a method that counts the numbers of online users in a room"""
        return OnlineUser.objects.filter(current_room=obj).count()
    
class OnlineUserSerializer(serializers.ModelSerializer):
    """a method serializer for online user"""
    user = serializers.StringRelatedField()
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    is_recently_active = serializers.SerializerMethodField()
    current_room_name = serializers.CharField(source='current_room.name')
    
    class Meta:
        """the table explains the additional behavioural structure"""
        model = OnlineUser
        fields = ['id', 'user', 'username', 'avatar', 'last_activity', 'current_room', 'current_room_name', 'is_recently_active']
        read_only_fields = ['id', 'last_activity']
    
        
    def get_is_recently_active(self, obj):
        """get the count of the online users"""
        return obj.is_recently_active()

class IsTypingSerializer(Serializers.ModelSerializer):
    """The serializer that shows information about typing"""
    
    