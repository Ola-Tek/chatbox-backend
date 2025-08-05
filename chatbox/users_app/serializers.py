from rest_framework import serializers
from .models import User, Conversation, Message

class UserSerializer(serializers.ModelSerializer):
    """convert the user infor into json format to make it readable"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar', 'password', 'bio', 'is_online', 'last_seen', 'created_at', 'status_message']
        read_only_fields = ['created_at', 'id', 'last_seen']
        extra_kwargs = {'password': {'write_only': True}} #it makes the password field only visible when you are registering or trying to update and not for GET operation
        
class UserProfileSerializer(serializers.ModelSerializer):
    """convers the user profile information to a json format"""
    class Meta:
        model = User
        fields = ['username', 'id', 'avatar', 'bio', 'is_online', 'last_seen', 'created_at', 'status_message']
        read_only_fields = ['created_at', 'id', 'last_seen' ]
        
#serializer for message
class MessageSerializer(serializers.ModelSerializer):
    """convert the message response into json response"""
    #this maps receiver to the receipient key that connected sender and user
    receiver = serializers.PrimaryKeyRelatedField(source='receipient', queryset=User.objects.all())
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'time_stamp', 'message_types', 'created_at', 'is_read'] #adds receiver even though it wasn't stated in the message model
        read_only_fields = ['id', 'created_at']
        
    def validate(self, attr): #attr represent a dictionary that consist of validated, serialized and deserialized input.
        """This is called immediately is_valid is called for your serializer"""
        sender = self.context['request'].user #provides the authenticated user who is the sender
        receiver = attr['receiver']
        
        #checks if the sender has been blocked by the receiver
        if sender in receiver.blocker_users.all():
            raise serializers.ValidationError("You have been blocked by this User")
        
        #checks if the receiver has been blocked by the sender
        if receiver in sender.blocker_users.all():
            raise serializers.ValidationError("You have blocked this user")
        return attr
    #to create and save the instance of the authenticated user who is the sender
    def create(self, valildated_data):
        """validate ensures that the right data is passed and also ensures that the blocked user can't receive a message from the user,
        but create helps to save it"""
        valildated_data['sender'] = self.context['request'].user
        return super().create(valildated_data)
                  
#serializer for conversation
class ConversationSerializer(serializers.ModelSerializer):
    """a serializer to handle the model conversation"""
    participant_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'paritcipant_count', 'title', 'is_group', 'updated_at', 'last_message', 'update_at']
        
    def get_participant_count(self, obj):
        """this is the field or function that participant_count point to, django will get the value of participant count from here,
        which is why we use SerializerMethodField"""
        return obj.participants.count()
    
    def get_last_message(self, obj):
        """This is a methofield serializer to get the last message which we would access through content """
        last_message = obj.messages.first()
        return {
            "content"  : last_message.content[:50] + ".......",
            "sender" : last_message.sender.username, 
            "created_at" : last_message.created_at
        } if last_message else None