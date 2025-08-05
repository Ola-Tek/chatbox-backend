from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(Notification)
class CustomAdminNotification(admin.ModelAdmin):
    """admin model for storing notification"""
    list_display = ['recipient', 'sender', 'notification_type', 'created_at', 'updated_at', 'title', 'notification_count']
    list_filter = ['is_read', 'notification_type', 'is_sent', 'read_at']
    search_fields = ['title', 'notification_type']
    readonly_fields = ['created_at', 'updated_at']
    
    #knowing how many notifications you have
    def notification_count(self, obj):
        """a method that counts all notification that the user has"""
        notification = Notification.objects.filter(recipient=obj.recipient).count()
        return notification
    notification_count.short_description = 'Notification count'
    
    def unread_notification_count(self, obj):
        """a method that accounts for the total number of notifications that hasn't been read"""
        unread_count = Notification.objects.filter(recipient=obj.recipient, is_read=False).count()#we filter using recipient to limit the unread message to the particular user
        return f"You have {unread_count} of unread messages"
    unread_notification_count.short_description = 'Unread Notification'
    
    
    fieldsets = [
        ('message', {
            'fields': ['title', 'message', 'recipient', 'sender']
        }),
        ('Notification Type', {
            'fields': ['notification_type'],
            'classes': ['collapse']
        }),
        ('Status', {
            'fields': ['is_read', 'is_sent']
        }),
        ('Time Stamp', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

@admin.register(NotificationSettings)
class CustomAdminNotificationSettings(admin.ModelAdmin):
    """The notification settings for admin interface"""
    list_display = ['recipient', 'sender', 'created_at', 'title', 'notification_type']
    list_filter = ['notification_type', 'is_read', 'created_at', 'is_sent']
    search_fields = ['title', 'message', 'recipient__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Info', {
            'fields': ['enable_push_notifications', 'enable_email_notifications']
        }),
        ('Quiet Hours', {
            'fields': ['quiet_hours_start', 'quiet_hours_end']
        }),
        ('Notification Types', {
            'fields': ['notify_new_messages', 'notify_friend_request', 'notify_mention', 'notify_group_invites'],
            'classes': ['collapse']
        }),
        ('Time Stamp', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    