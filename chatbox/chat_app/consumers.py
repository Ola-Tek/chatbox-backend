import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import TypingIndicator, ChatRoom, OnlineUser
from users_app.models import Message, Conversation

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """it manages the funtionality for the websocket, serves
    as the view funtion for the websocket"""
    async def connect(self):
        """this function is called when a client or browser tries to establish 
        a web socket connection with the server"""
        self.conversation_id = self.scope['url_route'], ['kwargs'], ['conversation_id']
        #extracts the conversation_id from the url route in routing.py
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']
        
        #check if the user is an authenticated user
        if self.user.is_anonymous:
            await self.close()
            return
        #needs to check for if the conversation can be accessed by the authenticated user
        has_access = await self.check_conversation_access()
        if not has_access:
            await self.close()
            return
        
        #the websocket connection is labeled as the channel_name
        #we add the rooom_group_name to the connection, so that all subscribed users can recieve the same message at the same time
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        #mark user to be online
        await self.set_user_online()
        
        #accept web socket connection
        await self.accept()
        
        #notify other clients that the user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type' : 'user_joined',
                'user_id' : self.user.id,
                'username' : self.user.username,    
            }
        )
    
    async def disconnect(self, close_code):
        """disconnect the connection"""
        #set the user to be offline
        #stop typing indicator
        #group_send
        await self.set_user_offline()
        
        #stop typing indicator
        await self.stop_typing_indicator()
        
        #notify the client that the user has left
        await self.channel_layer.group_send(
            self.room_group_name, {
                'type' : 'user_left',
                'user_id' : self.user.id,
                'username' : self.user.username,
            }
        )
        
        #leave group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
    async def receive(self, text_data):
        """asynchronous operation that handles the receive function - handles all kind of messages"""
        #the text_data is actually the raw data usually in json format parsed by the client to the server
        #so we need to be able to convert the raw data into a python objects so we can be able to access the type. The type will be defined in the front end
        #that's why we would be using json.loads(text_data)
        try:
            cleaned_data = json.loads(text_data)
            message_data_type = cleaned_data.get('type')
            
            if message_data_type == 'chat_message': #telling django to check the data type from the frontend side
                await self.handle_chat_message(cleaned_data)
            elif message_data_type == 'typing_start':
                await self.handle_typing_start() #the handling function cant take in a data cuz it handles when a user is typing, so no data inputed yet
            elif message_data_type == 'typing_stop':
                await self.handle_typing_stop()
            elif message_data_type == 'message_read':
                await self.handle_message_read(cleaned_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type' : 'error',
                'message' : 'Invalid Json' 
            }))
            
    async def handle_chat_message(self, data):
        """handle new chat message"""
        #-TRAIN OF THOUGHTS
        #check if data is not in db
        #check if the user is authenticated
        #also get the message type to be chat_message
        #if the data is not in db, it will save the message to the db
        message_content = data.get('message', '')
        message_type = data.get('message_type', 'text')
        
        if not message_content.strip(): #it tells the 
            return
            
        
        