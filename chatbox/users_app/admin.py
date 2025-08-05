from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.
@admin.register(User)
class CustomAdminUser(UserAdmin):
    """This inherits a class in the format of abstract user but registers the custom user model"""
    list_display = ['username', 'email', 'is_online', 'show_lastseen', 'date_joined', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_online', 'date_joined'] #is_staff, is_joined and is_superuser are inbuilt fields in django admin
    readonly_fields = ['email', 'username', 'bio']
    search_fields = ['date_joined', 'last_login', 'created_at', 'updated_at']
    
    #adding your custom fields to the class using Admin.Fieldsets = editing or updating a user
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('avatar', 'bio', 'is_online', 'last_seen', 'status_message')
        }),
    ('privacy settings', {
        'fields': ('show_onlinestatus', 'show_lastseen', 'blocker_users', 'allow_messages_from'),
        'classes': ('collapse',) #tells django to collapse this section
    }),
    ('time_stamp', {
        'fields': ('created_at', 'updated_at'),
        'classes': ('collapse',)
    })
    )
    
    #using our interface to create a new user
    fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('avatar', 'bio')
        }),
    )
    
@admin.register(Conversation)
class CustomAdminConversation(admin.ModelAdmin):
    """conversation for admin"""
    list_display = ['id', 'title', 'is_group', 'created_at', 'updated_at']
    list_filter = ['id', 'is_group', 'created_at']
    search_fields = ['title', 'participants__username']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['participants'] #nice widget for many to many field
    
    def participants_count(self, obj):
        """to define the number of participants taking part in a conversation, it's defined in the admin file because i want it to show in the 
        in the admin ui interface"""
        return obj.participants.count()
    participants_count.short_description = 'Participants' #it tells django admin to label the ui that calls participant_count method as participants
    
    fieldsets = [
        ('Basic info', {
            'fields': ['title', 'is_group', 'participants']
        }),
        
        ('Time Stamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    @admin.register(Message)
    class CustomAdminMessage(admin.ModelAdmin):
        """registers the message model in the admin"""
        list_display = ['sender', 'id', 'content_preview', 'created_at', 'is_read']
        list_filter = ['created_at', 'is_read', 'message_types']
        search_fields = ['content', 'sender__username', 'conversation__title']
        readonly_fields = ['created_at', 'updated_at']
        raw_id_fields = ['sender', 'conversation']
        
        def content_preview(self, obj):
            """shows the firest 50 characters for a content, so it can be previewed
            at list display"""
            if len(obj.content) > 50:
                return obj.content[:50] + "....."  
            else: 
                return obj.content
        content_preview.short_description = "Content Preview"
        
        fieldsets = [
            ('Message Info',{
                'fields': ['sender', 'conversation', 'message_types', 'content']
            }),
            ('Status', {
                'fields': ['is_read', 'is_delivered', 'is_edited'],
                'classes': ['collapse'],
            }),
            ('Attachments', {
                'fields': ['file_attachment'],
                'classes': ['collapse'],
            }),
        ]
        