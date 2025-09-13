from django.contrib import admin
from .models import OnlineUser, MessageDeliveryStatus, ChatRoom, TypingIndicator

# Register your models here.
@admin.register(ChatRoom)
class CustomAdminChatRoom(admin.ModelAdmin):
    """the admin custom for chatroom"""
    list_display = ['name', 'conversation', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'is_active']
    
    fieldsets = [
        ('Basic Info', {
            'fields': ['name', 'conversation']
        }),
        ('Status and Timestamp', {
            'fields': ['is_active', 'created_at'],
            'classes': ['collapse']
        }),
    ]

@admin.register(TypingIndicator)
class CustomAdminTypingIndicator(admin.ModelAdmin):
    """the admin structure for a typing indicator model defined in the models.py"""
    list_display = ['user', 'is_typing', 'conversation']
    list_filter = ['is_typing', 'user']
    search_fields = ['user', 'conversation']
    raw_id_fields = ['user', 'conversation']
    readonly_fields = ['is_typing', 'started_typing']
    
    fieldsets = [
        ('Basic Info', {
            'fields': ['user', 'conversation']
        }),
        ('Indicator and TimeStamp', {
            'fields': ['is_typing', 'started_typing'],
            'classes': ['collapse']
        }),
    ]

@admin.register(MessageDeliveryStatus)    
class CustomAdminDeliveryStatus(admin.ModelAdmin):
    """the custom admin structure for delivery status"""
    list_display = ['user', 'message', 'delivery_status']
    list_filter = ['delivery_status', 'user', 'timestamp']
    search_fields = ['user__username', 'message__id']
    raw_id_fields = ['user', 'message']
    readonly_fields = ['timestamp']
    
    fieldsets = [
        ('Basic Info', {
            'fields': ['user', 'message']
        }),
        ('Delivery Status', {
            'fields': ['delivery_status'],
            'classes': ['collapse'],
        }),
        ('Time Stamp', {
            'fields': ['timestamp']
        }),
    ]

@admin.register(OnlineUser)    
class CustomAdminOnlineUser(admin.ModelAdmin):
    """an custom admin structure for IsOnline"""
    list_display = ['user', 'current_room', 'socket_id', 'last_activity']
    list_filter = ['user', 'current_room']
    search_fields = ['user']
    raw_id_fields = ['user','current_room']
    readonly_fields = ['last_activity']
    
    fieldsets = [
        ('Basic Info', {
            'fields': ['user', 'current_room', 'socket_id']
        }),
        ('Activity', {
            'fields': ['last_activity']
        }),
    ]