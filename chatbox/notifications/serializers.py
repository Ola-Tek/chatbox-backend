from rest_framework import serializers
from .models import Notification, NotificationSettings
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationSenderSerializer(serializers.ModelSerializer):
    """convert the sender infor to a json fomat that can be used"""
    class Meta:
        model = User
        fields =  ['id', 'username', 'avatar']

class NotificationSerializer(serializers.ModelSerializer):
    """convert the notification info to a json format that can be used"""
    sender = NotificationSenderSerializer(read_only=True)
    time_ago = serializers.SerializerMethodField() #serializer method field are used for custom/computed fields, it doesn't exist on the database, but are gotten through a method defined
    class Meta:
        """the blueprint for the serializaer to follow"""
        model = Notification
        fields = ['recipient', 'sender', 'title', 'notification_type', 'created_at', 'related_conversation_id', 'related_message_id', 'is_read', 'is_created' 'time_ago']
        read_only_fields = ['created_at', 'message', 'read_at', 'id']

    def get_time_ago(self, obj):
        """get duration from which the notification was sent"""
        from django.utils import timezone
        from datetime import timedelta
        
        time_at_now = timezone()
        time_difference = time_at_now - obj.created_at
        
        if time_at_now > timedelta(minutes=1):
            return 'just now'
        elif time_at_now < timedelta(hours=1):
            minutes = int(time_at_now.total_seconds()) / 60
            return "{minutes}min ago"
        elif time_at_now < timedelta(days=1):
            hours = int(time_difference.total_seconds()) / 3600
            return "{hours}hr ago"
        else:
            days = time_difference.days()
            return "{days}days ago"
        
class CreateNotificationSerializer(serializers.ModelSerializer):
    """to create notifications"""
    class Meta:
        """extra stuff about """
        models = Notification
        fields = ['id', 'title', 'message', 'recipient', 'notification_type', 'related_conversation_id', 'related_message_id']
        read_only_fields = ['id']
        
    def create(self, validated_data):
        """the method that actually creates the notification"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['sender'] = request.user
        return super().create(validated_data)
        
class NotificationSettingsSerializer(serializers.ModelSerializer):
    """a serializer to show all settings"""
    class Meta:
        """extra infor about the table serializer"""
        models = NotificationSettings
        fields = ['enable_push_notifications', 
                  'enable_email_notification', 'notify_new_messages', 
                  'notify_friend_request', 'notify_mention', 
                  'notify_group_invites', 'quiet_hours_start', 
                  'quiet_hours_end']
        
    def validate(self, data):
        """validate quiet hours"""
        start = data.get('quiet_hours_start')
        end = data.get('quiet_hours_end')
        
        if start and end and start >= end:
            raise serializers.ValidationError("Quiet hours start hours must be before end time")
        return data
    
class BulkNotificationSerializer(serializers.Serializer):
    """a serializer for bulk notification"""
    recipients = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    
    notification_type = serializers.ChoiceField(choices=Notification.NOTIFICATION_TYPES)
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    related_message_id = serializers.IntegerField(required=False)
    related_conversation_id = serializers.IntegerField(required=False)