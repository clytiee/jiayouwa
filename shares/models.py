from django.db import models
from django.conf import settings


class Share(models.Model):
    """分享追踪"""
    
    share_id = models.CharField(max_length=20, unique=True, verbose_name='分享码')
    sharer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='分享者')
    resource = models.ForeignKey('resources.Resource', on_delete=models.CASCADE, verbose_name='分享的资源')
    channel = models.CharField(max_length=30, blank=True, verbose_name='分享渠道')
    
    click_count = models.IntegerField(default=0, verbose_name='点击数')
    register_count = models.IntegerField(default=0, verbose_name='注册数')
    download_count = models.IntegerField(default=0, verbose_name='下载数')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='分享时间')
    
    class Meta:
        db_table = 'shares_share'
        ordering = ['-created_at']
        verbose_name = '分享追踪'
        verbose_name_plural = '分享追踪'
        indexes = [
            models.Index(fields=['share_id']),
            models.Index(fields=['sharer', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.sharer.username} 分享了 {self.resource.title} ({self.share_id})"
    
    @property
    def share_url(self):
        """生成分享链接"""
        return f"/s/{self.share_id}"