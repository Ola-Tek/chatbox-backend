from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from users_app.models import Conversation
from django.utils.translation import gettext_lazy as _
from users_app.models import Conversation, Message

User = get_user_model()
# Create your models here.


class ChatRoom(models.Model):
    """a model for chat  rooms"""
    name = models.CharField(unique=True, max_length=50, verbose_name='Room Name')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    conversation = models.ForeignKey(Conversation, verbose_name=_("conversation"), on_delete=models.CASCADE)
    
    class Meta: #you use meta when you are trying to customize the behaviour of the database
        #in this case, by default django names my database in the format "appsname_modelsname"
        #something like chat_app_chatroom. So i am specifically telling django to name it 'chat_room' 
        """ extra information"""
        db_table = 'chat_room'
        indexes = [
            models.Index(fields=['conversation']),
        ]
    def __str__(self):
        return f'Room: {self.name}'
    


class OnlineUser(models.Model):
    """checks who is online, tracks users that is presently online"""
    user = models.OneToOneField(User, verbose_name=_("User"), on_delete=models.CASCADE, related_name='online_status')
    current_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    socket_id = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        """extra informatioin regarding the database table"""
        db_table = 'online_users'
        indexes = [
            models.Index(fields=['user', 'current_room'])
        ]
        
    def __str__(self):
        return f"{self.user.username} - online"
        
    def is_recently_active(self, minutes=5):
        """check if the user is recently active"""
        time_difference = timezone.now() - timezone.timedelta(minutes=minutes)
        return self.last_activity > time_difference
    


class TypingIndicator(models.Model):
    """tracks the user when he is typing"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    is_typing = models.BooleanField(default=True)
    started_typing = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        """additional behavioural information about the database"""
        constraints = [
            models.UniqueConstraint(fields=['user', 'conversation'], name='unique_typing_per_conversation')
        ]
        indexes = [
            models.Index(fields=['user','conversation'])
        ]
        db_table = 'typing_indicator'
        
        
    def __str__(self):
        return f"{self.user.username} typing in {self.conversation}"



class MessageDeliveryStatus(models.Model):
    """a model that keeps track of the status of the message during conversation"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]
    delivery_status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='sent')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        """extra information"""
        db_table = "message_delivery"
        constraints = [
            models.UniqueConstraint (fields=['message', 'user'], name='unique_message_user_status')
            ] #each user would have only a record of recorded message status
        #there would be no need to create another record of message read, when message sent has already being recorded, it would just update on the database 
       
    def __str__(self):
        return f"message {self.message.id} - {self.delivery_status} - by {self.user.username}" 