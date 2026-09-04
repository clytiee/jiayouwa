from django.db import models
from django.conf import settings


class BrowseHistory(models.Model):
    """浏览历史（用户展示用）"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户')
    resource = models.ForeignKey('resources.Resource', on_delete=models.CASCADE, verbose_name='资源')
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name='浏览时间')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    session_id = models.CharField(max_length=40, blank=True, null=True, verbose_name='会话ID')
    
    class Meta:
        db_table = 'recommendations_browsehistory'
        unique_together = ['user', 'resource']
        ordering = ['-viewed_at']
        verbose_name = '浏览历史'
        verbose_name_plural = '浏览历史'
        indexes = [
            models.Index(fields=['user', '-viewed_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} 浏览了 {self.resource.title}"