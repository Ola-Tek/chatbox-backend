from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.
class User(AbstractUser):
    """
    Abstract user is a django inbuilt functionality that helps to define a user
    with the following properties, username, email, password,is_createdat, and other important properties.
    """
    #adding other customized properties
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    bio = models.TextField(max_length=1000, blank=True)
    is_online =  models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)
    status_message = models.CharField(max_length=200, blank=True)
    
    #adding privacy settings
    show_onlinestatus = models.BooleanField(default=True)
    show_lastseen = models.BooleanField(default=True)
    
    #using a choice structure to determine who you want to block or see your messages
    PRIVACY_CHOICES = [
        ('everyone', 'Everyone'),
        ('contacts', 'Contacts Only'),
        ('nobody', 'Nobody'),
    ]
    allow_messages_from = models.CharField(
    max_length=13,
    choices=PRIVACY_CHOICES,
    default='everyone'
     )
    
    #blocked users
    blocker_users = models.ManyToManyField(
    'self',
    symmetrical=False,
    related_name='blocked_by',
    blank=True)
    
    #Tracks when user was created and updated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    #Tracks authentication settings, what would be used to log in to the account
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    #Giving the database additional structure
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['is_online'])
            #we don't need to index last seen, since we won't always be querying it
        ]
        
    def __str__(self):
        return f"{self.username}, ({self.email})"
    
    def block_user(self, user_to_block):
        """the business logic to block users"""
        self.blocker_users.add(user_to_block)
        shared_conversations = self.conversations.filter(participants=user_to_block, is_group=False)
        #if i want to delete shared_conversations later
        #shared_conversations.delete()
        
    def unblock_user(self, user_to_unblock):
        """it removes the blocked user from the list"""
        self.blocker_users.remove(user_to_unblock)
        return f"user unblocked successfully"
    
    def get_blocked_users(self):
        """it just get the list of blocked users"""
        self.blocker_users.all()
        
    def get_users_blockedby(self):
        """it get the list of users who blocked the user"""
        self.blocked_by.all()

#a conversation model, a conversation has so many messages
class Conversation(models.Model):
    """a model that describes conversation"""
    participants = models.ManyToManyField(User, related_name="conversations")
    title = models.CharField(max_length=255, blank=True)
    is_group = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    


#message model associated with the user
class Message(models.Model):
    """a model that describes the message class"""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('images', 'Images'),
        ('files', 'Files'),
        ('voice', 'Voice'),
    ]
    sender = models.ForeignKey(User, verbose_name=_("sender"), on_delete=models.CASCADE) #using '_' helps to translate the verbose name if another user with a different language visits the website
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages") #this represent one message in the Conversation
    #to get all messages in a conversation - conversation.messages.all
    #Conversation = conversation.messages.get(id=1) 
    content = models.TextField()
    time_stamp = models.DateTimeField(auto_now_add=True)
    message_types = models.CharField(max_length=255, choices=MESSAGE_TYPES, default='text')
    file_attachement = models.FileField(upload_to='/message_files', blank=True, null=True)
    
    #message status
    is_delivered = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    
    #check when it was updated or created
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    #giving the model an additional information
    class Meta:
        db_table = 'messages'
        ordering = ['-created_at']