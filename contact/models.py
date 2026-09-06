from django.db import models
from django.conf import settings


class ContactMessage(models.Model):
    """用户联系消息"""
    
    TYPE_CHOICES = (
        ('question', '问题咨询'),
        ('bug', 'BUG反馈'),
        ('suggestion', '功能建议'),
        ('other', '其他'),
    )
    
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('resolved', '已解决'),
        ('closed', '已关闭'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other', verbose_name='类型')
    title = models.CharField(max_length=100, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    contact = models.CharField(max_length=100, blank=True, verbose_name='联系方式（选填）')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    reply = models.TextField(blank=True, verbose_name='回复内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='提交时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'contact_message'
        ordering = ['-created_at']
        verbose_name = '联系消息'
        verbose_name_plural = '联系消息'
    
    def __str__(self):
        return f"{self.user.username}: {self.title[:30]}"

