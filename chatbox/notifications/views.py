from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from django.db.models import Q 
from .serializers import NotificationSenderSerializer, NotificationSettingsSerializer, BulkNotificationSerializer, NotificationSerializer, CreateNotificationSerializer
from .models import *
from django.contrib.auth import get_user_model
from rest_framework.response import Response

# Create your views here.
#create a crud operation:
#create notification
#delete notification
#read notification
#enable notification
#using api view

#@api_view(['GET'])
#@permission_classes([IsAuthenticated])
#def list_notifications(request):
#    """listing all notifications"""
#    serializer = NotificationSerializer
#    notifications = Notification.objects.filter(recipient=request.user)
#    serializer = NotificationSerializer(notifications, many=True)
#    return serializer.data
    

#@api_view(['POST'])
#@permission_classes([IsAuthenticated])
#def create_notifications(request):
#    """create notifications"""
#    serializer = CreateNotificationSerializer(data=request.data)
#    if serializer.is_valid:
#        serializer.save(sender=request.user)
#        return Response(serializer.data, status=status.HTTP_200_OK)
#   return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)

#@api_view(['DELETE'])
#@permission_classes([IsAuthenticated])
#def delete_notifications(request):
#    """Delete notifications"""
#    notifications = Notification.objects.filter(recipient=request.user)
#    deleted_count, _ = notifications.delete()
#    return Response (f"{deleted_count} notifications deleted", status=status.HTTP_200_OK)

#USING MODELVIEWSET
class NotificationViewSet(viewsets.ModelViewSet):
    """a viewset for models"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        notifications = Notification.objects.filter(recipient=self.request.user)
        return notifications
    
    def get_serializer_class(self, *args, **kwargs):
        """tells django the specific serializer to use for some action"""
        if action == 'create':
            return CreateNotificationSerializer
        return NotificationSerializer
    
    def perform_create(self, serializer): #allows you customize what should happen after it has been created
        """to create notification"""
        serializer.save(sender=self.request.user)#DRF already passes the validated serialized object
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """a method that explains if the message has been read"""
        notification_object = self.get_object()
        serializer = self.get_serializer(notification_object)
        notification_object.mark_read() #there is a logical method in 
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """a method that marks all the messages read"""
        queryset = self.get_queryset()
        queryset.update(is_read=True, read_at=timezone.now())
        
        #after updating we have to refresh the database by calling the the queryset again
        updated_queryset = self.get_queryset()
        serializer = self.get_serializer(updated_queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """a method that actually counts the number of unread notifications"""
        unread_notifications = Notification.objects.filter(is_read=False, recipient=self.request.user)
        count = unread_notifications.count()
        return Response({"message" : f"You have {count} unread notifications"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """a method that gets all unread messages"""
        unread = Notification.objects.filter(is_read=False, recipient=self.request.user)
        serializer = self.get_serializer(unread, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def send_bulk_notifications(self, request):
        """send bulk notifications"""
        serializer = BulkNotificationSerializer(data=request.data)
        
        #check if all informations are correctly filled aand then get all recipients to loop through
        if serializer.is_valid():
            data = serializer.validated_data
            recipients = data.pop('recipients')
            sender = self.request.user
            
            #create a list of notifications that would save the notification objects created for each id
            notifications =[]
            #create a Notification object
            for recipient_id in recipients: #loops through the whole recipient 
                notifications.append(Notification(
                    recipient_id=recipient_id, sender=sender, **data)
                )
            
            #after creating a notification object for each recipient, you have to then use the objects.bulk_create to be able to be saved on the database
            bulk_notification = Notification.objects.bulk_create(notifications)
            return Response({'message': f'{len(bulk_notification)} notifications sent',
                             'count' : len(bulk_notification)}, status=status.HTTP_200_OK)
        return Response({'message': 'information is invalid'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def clear_read(self, request):
        """clears all read messages"""
        #we have to get all read messages
        read_notifications = self.get_queryset().filter(is_read=True)
        counted_notifications = read_notifications.count()
        read_notifications.delete()
        return Response({'message': f'{counted_notifications} notifications has been deleted',
                         'count': counted_notifications}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])    
    def list_notifications(self, request, *args, **kwargs):
        """list all notifications"""
        notifications = self.get_queryset()    
        #filter by notification types
        notification_type = request.query_params.get('notification_type')
        if notification_type:
            queryset = notifications.filter(notification_type)
            return queryset
        
        #filter by is_read
        is_read = request.query_params.get('is_read')
        if is_read:
            is_read_bool = is_read.lower() == 'true'
            queryset = notifications.filter(is_read=is_read_bool)
            return queryset
        
        #pagination
        page = self.paginate_queryset(notifications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(notifications)    
        return Response(serializer.data)

class NotificationSettingsViewSet(viewsets.ModelViewSet):
    """a view class for notification settings logic"""
    serializer_class = NotificationSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """this get the whole queryset for notificationsettings of the requested user"""
        return NotificationSettings.objects.filter(user=self.request.user)
    
    def get_object(self):
        """get or create notification settings for the current user
        in real world analogy, when the user logs in, it checks if the user
        has a record of notification settings and if not, it creates one for the user
        so he can be able to edit"""
        settings, created = NotificationSettings.objects.get_or_create(user=self.request.user) #created is an inbuilt boolean value returned by get_or_create that returns true or false if the notification settings has been created
        return settings
    
    @action(detail=False, methods=['get'])
    def my_settings(self, request):
        """to get your own customized settings"""
        settings = self.get_object()
        serializer = NotificationSettingsSerializer(settings)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'post'])
    def update_settings(self, request):
        """to update the settings"""
        settings = self.get_object()
        serializer = self.get_serializer(settings, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({'message': 'invalid information'}, serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def reset_default_settings(self, request):
        """A method that reset notification settings to the default values"""
        settings = self.get_object()
        
        #setting everything to a default value of true and none where necessary
        NotificationSettings.enable_push_notifications = True
        NotificationSettings.enable_email_notifications = True
        NotificationSettings.notify_friend_request = True
        NotificationSettings.notify_group_invites = True
        NotificationSettings.notify_new_messages = True
        NotificationSettings.notify_mention = True
        NotificationSettings.quiet_hours_start = None
        NotificationSettings.quiet_hours_end = None
        
        serializer = self.get_serializer(settings)
        return Response({'message': 'settings reset to default', 'settings': serializer.data}, status=status.HTTP_200_OK)