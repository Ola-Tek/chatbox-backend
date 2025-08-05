from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from users_app.models import Conversation
from django.utils.translation import gettext_lazy as _

user = get_user_model()
# Create your models here.
class chatroom(models.Model):
    """a model for chat  rooms"""
    name = models.CharField(unique=True, max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    conversation = models.ForeignKey(Conversation, verbose_name=_("conversation"), on_delete=models.CASCADE)
    
    class Meta: #you use meta when you are trying to customize the behaviour of the database
        #in this case, by default django names my database in the format "appsname_modelsname"
        #something like chat_app_chatroom. So i am specifically telling django to name it 'chat_room' 
        """ extra information"""
        db_table = 'chat_room'
        
    def __str__(self):
        return f'Room: {self.name}'
