from django.db import models
from django.conf import settings


class Notification(models.Model):
    """站内私信"""
    
    TYPE_CHOICES = (
        ('system', '系统消息'),
        ('audit_pass', '审核通过'),
        ('audit_reject', '审核不通过'),
        ('comment', '评论通知'),
        ('follow', '关注通知'),
        ('like', '点赞通知'),
    )
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_notifications',
        verbose_name='接收者'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True,
        on_delete=models.SET_NULL, 
        related_name='sent_notifications',
        verbose_name='发送者'
    )
    title = models.CharField(max_length=100, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    message_type = models.CharField(
        max_length=30, 
        choices=TYPE_CHOICES, 
        default='system',
        verbose_name='消息类型'
    )
    related_resource = models.ForeignKey(
        'resources.Resource', 
        null=True, 
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='关联资源'
    )
    related_comment = models.ForeignKey(
        'resources.Comment', 
        null=True, 
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='关联评论'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')
    
    class Meta:
        db_table = 'notifications_notification'
        ordering = ['-created_at']
        verbose_name = '站内私信'
        verbose_name_plural = '站内私信'
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.recipient.username}: {self.title}"