from django.shortcuts import render
from .serializers import *
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import *
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from datetime import timedelta, timezone

# Create your views here.
class ChatRoomViewSet(viewsets.ModelViewSet):
    """the viewset that manages chatroom"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatRoomSerializer
    queryset = ChatRoom.objects.all()
    
    def get_queryset(self):
        """get all active chatrooms"""
        return ChatRoom.objects.filter(is_active=True)
    
    @action(detail=True, methods='post')
    def join_chatroom(self, request, pk=None):
        """joining a chatroom"""
        chat_room = self.get_object
        user = request.user
        
        online_user, created = OnlineUser.objects.update_or_create(
            user=user,
            defaults={
                'current_room': chat_room,
                'last_activity': timezone.now()
            }
        )
        return Response({
            'message': f"joined {chat_room.name} successfully!",
            'chat room': ChatRoomSerializer(chat_room).data,
            'created': created
        })
    
    @action(detail=True, methods=['post'])    
    def leave_chatroom(self, request, pk=None):
        """on how to leave the chatroom"""
        user = request.user
        chat_room = self.get_object()
        
        try: 
            requested_user = OnlineUser.objects.get(user=user, current_room=chat_room)
            requested_user.current_room == None
            requested_user.save()
            
            return Response ({'message': f'{user} has sucessfully left the group'})
        except requested_user.DoesNotExist:
            return Response({
                'message': 'You are not in this room'
            }, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=True, methods=['get'])
    def online_user(self, request, pk=None):
        """get the total number of online users in a chat room"""
        chat_room = self.get_object()
        
        online_user = OnlineUser.objects.filter(current_room=chat_room)
        serializer = OnlineUserSerializer(online_user, many=True)
        return Response({
            serializer.data()
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])    
    def active_rooms(self, request):
        """get rooms where a current user is active"""
        user = request.user
        rooms = ChatRoom.objects.filter(user=user, is_active=True)
        
        if rooms.exists(): 
            serializer = ChatRoomSerializer(rooms, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
    
        return Response({'message':'You are not active in any room'}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def my_room(self, request):
        """get the room where an active user is"""
        user = request.user
        online_user = OnlineUser.objects.get(user=user)
        
        try:
            
            if online_user.current_room:
                room_serializer = ChatRoomSerializer(online_user.current_room)
                return Response (room_serializer.data)
            else:
                return Response({'message': 'Not in my room!'})
            
        except online_user.DoesNotExist:
            return Response ({'message': 'the user is not onine in this room'})
        
class OnlineUserViewSet(viewsets.ModelViewSet):
    """the viewset that manages online users"""
    queryset = OnlineUser.objects.all()
    serializer_class = OnlineUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    
    def get_queryset(self):
        """get the query set of all online users in the past five minutes"""
        return OnlineUser.objects.filter(last_activity__gte=timezone.now() - timedelta(minutes=5))
    
    @action(detail=False, methods=['post'])
    def update_activity(self, request):
        """update the queryset"""
        #check the last activity
        #if the last activity is greater than five minutes
        #then check if the user is online/active
        #if he is then update it to the current time frame
        online_user, created = OnlineUser.objects.filter(
            user=request.user,
            defaults={'last_activity': timezone.now()}
        )
        serializer = self.get_serializer(online_user)
        return Response(serializer.data)
    
    @action(detail=False, methods='get')
    def get_conversation_users(self, request):
        """get online users for a specific conversation"""
        #thinking frame: get the online users by filtering the conversation out
        #we are supposed to attach a conversation id to online user
        #we had to get the conversation id from the request
        conversation_id = request.query_params.get('conversation_id')
        if conversation_id:
            conversation_user = self.get_queryset().filter(current_room__conversation_id=conversation_id)
            serializer = self.get_serializer(conversation_user, many=True)
            return Response({'online users': serializer.data,
                             'conversation id': conversation_id,
                             'no of online users': len(serializer.data)}, status=status.HTTP_200_OK)
        return Response({'error': 'there must be a conversation id' }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'])
    def set_offline(self, request):
        """to set an online user to be offline"""
        #thinking frame: so since online user represent the user online, deleting the user online means it would be offline
        #hope it won't cause a bottle neck in our database when we always want to delete a user when they are offline
        #we first of all have to get the user that is making the request, the person is an online user
        try:
            online_user = OnlineUser.objects.get(user=request.user)
            online_user.delete()
            return Response({'message': 'user has been set to offline'}, status=status.HTTP_200_OK)
        except online_user.DoesNotExist:
            return Response({'message': 'User was not online'})
        
class TypingIndicatorViewSet(viewsets.ModelViewSet):
    """a logic that handles the typing indicator"""
    queryset = TypingIndicator.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TypingIndicatorSerializer
    
    def get_queryset(self):
        """returns the typing indicator for a user in a particular conversation"""
        conversation_id = self.request.query_params.get('conversation_id')
        if conversation_id:
            return TypingIndicator.objects.filter(is_typing=True, conversation_id=conversation_id).exclude(user=self.request.user)
        return TypingIndicator.objects.none() #returns an empty queryset
    
    def perform_create(self, serializer):
        """it's usually used when you need it to carry out a task before saving,
        in this case, you are setting the user to be a requested user"""
        #why do we need to set the user before we create a typing indicator instance?
        #because we want to make sure that the typing instance created is tied to the requested user,
        #and we can only get it by 
        serializer.save(user=self.request.user)
    @action(detail=False, methods=['post'])    
    def start_typing(self, request):
        """start typing in a conversation"""
        #in order to incorportate start typing logic, you have to get the conversation id from the request
        #not just conversation_id, get the user
        serializer = TypingIndicatorSerializer(data=request.data)
        if serializer.is_valid():
            conversation_id = serializer.validated_data('conversation_id')
            typing_indicator, created = TypingIndicator.objects.update_or_create(
                conversation_id=conversation_id,
                user=request.user,
                defaults={'is_typing': True}
            )
            response_serializer = TypingIndicatorSerializer(typing_indicator)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_200_OK)
    
    
    def stop_typing(self, request):
        """stop typping in a conversation"""
        #we have to get the conversation id  from the serialized data
        serializer = TypingIndicatorSerializer(data=request.data)
        
        if serializer.is_valid():
            conversation_id = serializer.validated_data('conversation_id')
            TypingIndicator.objects.filter(
                conversation_id=conversation_id,
                user=request.user,
                defaults={'is_typing': False}
            ).delete()
            return Response({'message': 'stopped typing'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def who_is_typing(self, request):
        """get who is typing in a conversation"""
        #get the conversation
        #get the user
        conversation_id = self.request.query_params.get('conversation_id')
        if not conversation_id:
            """we want to handle and make sure that there is a conversation before we can be able
            to find who is typing"""
            return Response({'error': 'conversation id required'}, status=status.HTTP_400_BAD_REQUEST)
        typing_users = TypingIndicator.objects.filter(
            conversation_id=conversation_id,
            is_typing=True,
        ).exclude(user=request.user)
        
        serializer = TypingIndicator(typing_users, many=True)
        return Response({'conversation_id': conversation_id,
                         'who_is_typing': serializer.data,
                         'count': len(serializer.data)}, status=status.HTTP_200_OK)
        
class MessageDeliveryStatusViewSet(viewsets.ModelViewSet):
    """manages the functional viewset of message delivery"""
    queryset = MessageDeliveryStatus.objects.all()
    serializer_class = MessageDeliveryStatusSerializer
    permission_classes = permissions.IsAuthenticated
    
    def get_queryset(self):
        """return delivery status for a particular message"""
        message_id = self.request.query_params.get('message_id')
        if message_id:
            return MessageDeliveryStatus.objects.filter(message_id=message_id)
        return MessageDeliveryStatus.objects.none()
    
    @action(detail=False, methods=['post'])
    def mark_delivered(self, request):
        """marks a particular message as read"""
        serializer = BulkMessageStatusSerializer(data=request.data)
        
        
        if serializer.is_valid():
            message_ids = serializer.validated_data['message_id']
            
            #tracks created instances, for easy debug
            updated_count = 0
            
            for message_id in message_ids:
                updated_status, created = MessageDeliveryStatus.objects.update_or_create(
                    message_id=message_id,
                    user=request.user,
                    defaults={'delivery_status': 'delivered'}
                )
                if created or updated_status.delivery_status != 'delivered':
                    updated_count += 1
            return Response({'message': f'{updated_count} messages were delivered',
                                 'updated_count': updated_count})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """marks messages as read"""
        #first of all have to get the serialized request data, which serializer? - use bulk serializer
        #check if the serialized data is valid
        #supposed to get the message_id from the serialized data
        #use the validated data to create or update the user, message_id and status
        serializer = BulkMessageStatusSerializer(data=request.data)
        
        if serializer.is_valid():
            """get the message from the serialized data"""
            message_ids = serializer.validated_data['message_id']
            updated_count = 0 #to track the number of messages that has probably been created and not on read mode
            
            for message_id in message_ids:
                updated_status, created = MessageDeliveryStatus.objects.update_or_create(
                    user=request.user,
                    message_id=message_id,
                    defaults={'delivery_status': 'read'},
                )
                
                #checks if created or the updated status is not on read and increments
                if created or updated_status.delivery_status != 'read':
                    updated_count += 1
            return Response({'message': f'{updated_count} messages has been read',
                             'updated_count': updated_count}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def message_status(self,request):
        """get the delivery status for a particular message"""
        #you have to get the particular message_id from the request
        #confirm that there is a message_id, if not return an error message for geting the message id
        # then filter the message, from the options for user, and status to provide the particular delivery status
        #you want to return the serialized data, so you have to serialize the particular message you have filtered
        message_id = request.query_params.get('message_id')
    
        if not message_id:
            return Response({'error': 'message_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        status_message = MessageDeliveryStatus.objects.filter(
            user=request.user,
            message_id=message_id,   
        )
        if not status_message.exists():
                return Response({'message': 'this message_id do not have a delivery status'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = MessageDeliveryStatusSerializer(status_message, many=True)
        return Response({'message': serializer.data}, status=status.HTTP_200_OK)
        
        
            
        
        
                
            
        
