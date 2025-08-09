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


class TypingIndicatorSerializer(serializers.ModelSerializer):
    """The serializer that shows information about typing"""
    user = serializers.StringRelatedField()
    username = serializers.CharField(source='user.username', read_only=True)
    avartar = serializers.ImageField(source='user.avatar', read_only=True)
    
    class Meta:
        """additional information concerning the information"""
        model = TypingIndicator
        fields = ['id', 'user', 'username', 'avatar' 'is_typing', 'conversation_id']
        read_only = ['id', 'started_typing']
        
    def create(self, validated_data):
        """it get the user validated data cuz there are some information that might be in the serializer
        not in the model"""
        user = validated_data['user']
        conversation_id = validated_data['conversation_id']
        
        #create or update existing user data
        typing_indicator, created = TypingIndicator.objects.update_or_create(
            user=user,
            conversation_id=conversation_id,
            defaults=validated_data
        )
        return typing_indicator
    

class MessageDeliveryStatusSerializer(serializers.ModelSerializer):
    """serializer for message delivery status"""
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = MessageDeliveryStatus
        fields = ['user', 'username' 'message', 'delivery_status', 'timestamp']
        read_only = ['id','timestamp']


class UserOnlinePresenceSerializer(serializers.Serializer):
    """a serializer class that shows the online presence of a user in a room"""
    user = serializers.StringRelatedField()
    avatar = serializers.ImageField(source='user.avatar')
    current_room = serializers.CharField(allow_null=True)
    is_online = serializers.BooleanField()
    last_seen = serializers.DateTimeField()
    

class ConversationOnlineUserSerializer(serializers.Serializer):
    """a serializer class that shows the number of online users"""
    online_user = OnlineUserSerializer(many=True, read_only=True)
    conversation_id = serializers.IntegerField()
    total_count = serializers.IntegerField()
    online_count = serializers.IntegerField()
    

class TypingStatusSerializer(serializers.Serializer):
    """a serializer class that typing status users"""
    conversation_id = serializers.IntegerField()
    is_typing = serializers.BooleanField()
    
class BulkMessageStatusSerializer(serializers.Serializer):
    """serializer for bulk status"""
    message_id = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    message_status = serializers.ChoiceField(choices=MessageDeliveryStatus.STATUS_CHOICES)
    
    def create(self, validated_value):
        """validate status progression: sent->delivered->read"""
        if validated_value  not in ['sent', 'delivered', 'read']:
            raise serializers.ValidationError('Invalid Status')
        return validated_value
    