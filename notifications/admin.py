from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'is_read', 'message_type', 'created_at']
    list_filter = ['is_read', 'message_type']
    search_fields = ['title', 'content', 'recipient__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('消息信息', {
            'fields': ('recipient', 'sender', 'title', 'content', 'message_type')
        }),
        ('状态', {
            'fields': ('is_read', 'created_at')
        }),
        ('关联', {
            'fields': ('related_resource', 'related_comment'),
            'classes': ('collapse',)
        }),
    )