from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view
from django.db.models import Q 
from .serializers import ConversationSerializer, UserSerializer
from .models import *
from django.contrib.auth import get_user_model
from rest_framework.response import Response
# Create your views here.

user = get_user_model

class ConversationViewSet(viewsets.ModelViewSet):
    """using a viewset operation to build a CRUD operation for a conversation"""
    serializer_class = ConversationSerializer #tells django how to convert responses or post request to json format
    permission_classes = [permissions.isAuthenticated] #sets permission to tell django that only logged in user can access this view function
    
    #get_queryset is also an inbuilt hook for drf that tends to get or retrieve
    def get_queryset(self):
        #return conversation where user is a participant
        return Conversation.objects.filter(participants = self.request.user) #self.request.user represent the user who made the request
    
    #perform_create is a built in hook in drf that tends to post request
    def perform_create(self, serializer):
        #add the user while creating a new conversation
        conversation = serializer.save()
        return conversation.participants.add(self.request.user)
    
    @action(detail=True, methods='POST')
    def add_participants(self, request, pk=None):
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        #add validation and business logic under it
        return Response({"status" : "Participant added"})
    
class MessageViewSet(viewsets.ModelViewSet):
    """a view function to handle listing a message and to get a message using get_queryset"""
    def get_queryset(self):
        conversation_id = self.request.query_params.get("conversation_id")
        return Message.objects.filter(conversation_id=conversation_id)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset) #this get the paginated queryset, it's not yet a json friendly format, so we have to convert it
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

class UserViewSet(viewsets.ModelViewSet):
    """handles the business logic of the user model and also to handle authentication"""
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.action == 'list':
            return User.objects.filter(conversations__participants=self.request.user).distinct()
        else:
            return super().get_queryset()
        
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.actions in ['update', 'destroy', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes] #iterating through permission_classes and telling it to instatiate the objects in the permission class
        
    def get_object(self):
        """
        a view function under user that get a user profile, or checks your user profile for up dating
        or editing.
        """
        user = self.request.user
        if self.action in ['update', 'destroy', 'partial_update', 'retrieve']:
            return user
        return super().get_object() #this tells DRF that for any action like create and list, it could get any user according to the pk.
    
    @action(detail=False, method=['get'])
    def me(self, request):
        """Get the user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    #change password
    @action(detail=False, method=['post'])
    def changepassword(self, request):
        """a view funtion to changepassword"""
        new_password = request.data.get('new_password')
        old_password = request.data.get('old_password')
        
        if not request.user.check_password(old_password):#CHECK_PASSWORD
            return Response({'error': 'Invalid Password'}, status=status.HTTP_400_BAD_REQUEST)
        
        request.user.set_password(new_password)
        request.user.save()
        return Response({'message': 'password changed successfully!'}, status=status.HTTP_200_OK)
    
    #adds a user to a list of blocked users
    @action(detail=False, methods='post')
    def block_user(self, request, pk=None):
        """blocking a user"""
        user_to_block = self.get_object()
        if user_to_block == self.request.user:
            return Response ({"message" : "You can't block Yourself"})
        request.user.blocker_users.add(user_to_block)
        return Response ({"message" : "user blocked successfully"})
    
    #adds a user to a list of unblocked users
    @action(detail=True, methods='post')
    def unblock_user(self, request, pk=None):
        user_to_unblock = self.get_object()
        request.user.blocker_users.remove(user_to_unblock)
        return Response ({"message" : "user successfully unblocked"})
    
    #search for users
    @action(detail=False, methods=['get'], url_path='search')
    @permission_classes[permissions.IsAuthenticated]
    def search_users(self, request):
        """a function that searches for users"""
        query = request.query_params.get('query', '') #tries to get the parameter of the request called query
        if query:
            requested_user = User.objects.filter(username__icontains=query).exclude(id=request.user.id)
            serializer_updated = UserSerializer(requested_user, many=True)
            return Response(serializer_updated.data)
        if len(query) < 2:
            return Response({'message': 'search query must be more than two characters'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'Please provide a search query'}, status=status.HTTP_400_BAD_REQUEST)
        
        
        
            
    
    
                
     
