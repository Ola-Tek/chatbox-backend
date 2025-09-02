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
        #needs to check for if the user is part of the conversation
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
            elif message_data_type == 'start_typing':
                await self.handle_start_typing() #the handling function cant take in a data cuz it handles when a user is typing, so no data inputed yet
            elif message_data_type == 'stop_typing':
                await self.handle_stop_typing()
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
        
        if not message_content.strip(): #strip removes all trailing white spaces, so if after removing all white spaces you have a message content => "". Then it would fail silently, cuz you don't want to send an empty message of white spaces
            return
            
        #we have to save  the new message after confirming the message_type
        #message is an instance of Message model cuz save_message returns a created row of message in the database
        message = await self.save_message(message_content, message_type)
        
        #after message has been saved we want to then broadcast the message
        if message: 
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type' : 'chat_message',
                    'message_id' : message.id,
                    'message_type' : message_type,
                    'message' : message_content,
                    'user_id' : self.user.id,
                    'username' : self.user.username,
                    'avatar' : self.user.avatar.url if self.user.avatar else None,
                    'time_stamp' : message.time_stamp.isoformat(), #this refers to the timestamp designed in your model, isformat changes datetime field to a stringify field, cuz datetime field can not be passed in the websocket
                }
            )
            
    async def handle_start_typing(self):
        """Handle start typing"""
        #-TRAIN OF THOUGHTS
        #1. We have to show the user who is about sending a message after a ws connection has been initialized
        #2. set is_typing to be True
        #3. how can we get is_typing - There should be a typing indicator instance that can access is typing and set it to be True
        #4. after setting the typing indicator to be true we have to broadcast it to users on the same broadcast channel - channel_name/room_group_name
        
        await self.set_typing_indicator(True) #where set_typing_indicator will be an instance of typing_indicator which will either be created or updated
        
        #broadcast to others in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type' : 'typing_indicator',
                'user_id' : self.user.id,
                'username' : self.user.username,
                'is_typing' : True, 
            }
        )
        
    async def handle_stop_typing(self):
        """handles when the client stop typing"""
        #-TRAIN OF THOUGHTS
        #1. We have to set typing indicator to be false
        #2. access is_typing to be false
        #3. broadcast to others that you stopped typing
        
        await self.set_typing_indicator(False)
        
        #notify others that you stopped typing
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type' : 'typing_indicator',
                'user_id' : self.user.id,
                'username' : self.user.username,
                'is_typing' : False,
            }
        )
        
    async def handle_message_read(self, data):
        """handles all read messages status"""
        #-TRAIN OF THOUGHTS
        #1. set status of read message to be true - it could be another asynchronous function
        #2. you have to get the message_id
        #3. broadcast or notify that it has been read
        
        message_id = await data.get('message_id')
        
        if message_id:
            await self.mark_message_read(message_id)
            
        #notify that the message has been read
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type' : 'message_read',
                'message_id' : message_id,
                'read_by_user_id' : self.user.id,
                'read_by_username' : self.user.username,
            }
        )
        
    #EVENT HANDLERS FOR THE TYPE, IT TELLS DJANGO WHAT TO DO WHEN IT COMES ACROSS A PARTICULAR TYPE
    async def chat_message(self, event):
        """send chat message to each personal websocket connection"""
        #1. events represents an instance of a message sent over a connection
        #2. Purpose of this is to ensure when a user sends a message, he doesn't get the same message back
        
        if event['user_id'] != self.user.id:
            #specifies that the user who sent the message is not the same as the user who is receiving it
            #then it would broadcast it
            await self.send(text_data=json.dumps({
               'type' : 'chat_message',
               'message_id' : event['message_id'],
               'message' : event['message'],
               'message_type' : event['message_type'],
               'user_id' : event['user_id'],
               'username' : event['username'],
               'avartar' : event['avartar'],
               'timestamp' : event['timestamp'], 
            }))
    async def typing_indicator(self, event):
        """send typing indicator to websocket"""
        #we dont want to send typing indicator back to the sender, so we have to filter that out
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type' : 'typing_indicator',
                'user_id' : event['user_id'],
                'username' : event['username'],
                'is_typing' : event['is_typing']
            }))
            
    async def message_read(self, event):
        """send a message read status to the websocket"""
        #1. we have to make sure that the user whose message has been read is not also receiving his own read message status
        #2. we also have to change the status to show that it has been read, especially if its defaulted at false
        #3. there is a delivery status in message, so we access it by creating an instance of it
        
        await self.send(text_data=json.dumps({
            'type' : 'message_read',
            'message_id' : event['message_id'],
            'read_by_user_id' : event['read_by_user_id'],
            'read_by_username' : event['read_by_username'],
        }))
            
    async def user_joined(self, event):
        """send user joined notification across the websocket"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type' : 'user_joined',
                'user_id' : event['user_id'],
                'username' : event['username'],
            }))
            
    async def user_left(self, event):
        """send the user that left over the websocket"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type' : 'user_left',
                'user_id' : event['user_id'],
                'username' : event['username'],
            }))
            
    #DATABASE OPERATIONS, SINCE IT'S AN ASYNCHRONOUS OPERATION WE WOULD NEED TO WRAP IT IN A DATA_SYNC_TO_ASYNC DECORATOR
    @database_sync_to_async
    async def check_conversation_access(self):
        """check if the user has access to the conversation"""
        #1.we have to get the conversation id
        #2. we have to also check if user is in the same room as where the conversation was made
        #3. to get the conversation, we would use the get function to query the database
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return self.user in conversation.participants.all()
        except Conversation.DoesNotExist:
            return False
        
    @database_sync_to_async
    async def save_message(self, message, message_type='text'):
        """save the message on the database"""
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.update_or_create
    
        