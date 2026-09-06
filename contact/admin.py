from django.contrib import admin
from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'type', 'status', 'created_at']
    list_filter = ['status', 'type', 'created_at']
    search_fields = ['title', 'content', 'user__username']
    readonly_fields = ['user', 'type', 'title', 'content', 'contact', 'created_at', 'updated_at']
    
    fieldsets = (
        ('消息信息', {
            'fields': ('user', 'type', 'title', 'content', 'contact')
        }),
        ('处理状态', {
            'fields': ('status', 'reply')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_processing', 'mark_resolved']
    
    def mark_processing(self, request, queryset):
        queryset.update(status='processing')
        self.message_user(request, '✅ 已标记为处理中')
    mark_processing.short_description = '标记为处理中'
    
    def mark_resolved(self, request, queryset):
        queryset.update(status='resolved')
        self.message_user(request, '✅ 已标记为已解决')
    mark_resolved.short_description = '标记为已解决'
    
    def save_model(self, request, obj, form, change):
        """保存时发送回复通知给用户"""
        # 获取原始对象（如果是修改）
        original = None
        if obj.pk:
            original = ContactMessage.objects.get(pk=obj.pk)
        
        # 保存对象
        super().save_model(request, obj, form, change)
        
        # ✅ 只在以下情况发送通知：
        # 1. 有回复内容
        # 2. 是修改（不是新建）
        # 3. 回复内容发生了变化
        if obj.reply and change and original and original.reply != obj.reply:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=obj.user,
                sender=request.user,
                title=f'📩 你的消息已回复：{obj.title[:30]}',
                content=f'管理员回复：\n{obj.reply[:200]}',
                message_type='system',
            )