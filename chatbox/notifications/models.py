from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from users_app.models import Conversation, Message
# Create your models here.

User = get_user_model()

class Notification(models.Model):
    """model for storing notification"""
    
    #create different types of notification
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('friend_request', 'Friend Request'),
        ('mention', 'Mention'),
        ('group_invite', 'Group Invitation'),
        ('typing', 'Typing'),
        ('user_online', 'User Online'),
    ]
    recipient = models.ForeignKey(User, verbose_name=_("Recipient"), on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notification', null=True, blank=True)
    notification_type = models.CharField(max_length=255, choices=NOTIFICATION_TYPES, default='message')
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_conversation = models.ForeignKey(Conversation, null=True, blank=True, on_delete=models.CASCADE, related_name='notifications')
    related_message = models.ForeignKey(Message, null=True, blank=True, on_delete=models.CASCADE, related_name='notifications')
    
    #notification related to conversation and message
    
    #status field
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False) #for push notifications
    
    #timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    #give the table extra information using meta
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    #method that marks message that has been read
    def mark_read(self):
        """mark notification as read"""
        if not self.is_read == True:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
            
class NotificationSettings(models.Model):
    """specifies user's preference for notification settings"""
    user = models.OneToOneField(User, verbose_name=_("User"), on_delete=models.CASCADE, related_name='notification_settings')
    
    #push notification settings
    enable_push_notifications = models.BooleanField(default=True)
    enable_email_notifications = models.BooleanField(default=True)
    
    #specific notification types
    notify_new_messages = models.BooleanField(default=True)
    notify_friend_request = models.BooleanField(default=True)
    notify_mention = models.BooleanField(default=True)
    notify_group_invites = models.BooleanField(default=True)
    
    #time when the user does not want to receive any notification
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """adding extra information for the database table"""
        ordering = ["-created_at"]
        db_table = 'notification_setting'
        
        def __str__(self):
            return f"settings for {self.user.username}"  
    
            