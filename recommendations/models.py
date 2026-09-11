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


class Behavior(models.Model):
    """
    用户行为记录表（推荐系统专用）
    
    注意：此表仅用于推荐系统训练，不提供前端展示功能。
    未来可迁移至 Redis + 日志文件 / 时序数据库。
    """
    
    ACTION_CHOICES = (
        # 资源相关
        ('view', '浏览'),
        ('click', '点击'),
        ('search', '搜索'),
        ('collect', '收藏'),
        ('upvote', '资源点赞'),
        ('downvote', '资源点踩'),
        ('download', '下载'),
        ('free_download', '免费下载'),
        ('open_link', '打开链接'),
        ('copy_link', '复制链接'),
        ('copy_code', '复制提取码'),
        ('share', '分享'),
        ('comment', '评论'),
        ('comment_up', '评论点赞'),
        ('comment_down', '评论点踩'),

        # 用户相关
        ('register', '注册'),
        ('login', '登录'),
        ('logout', '退出登录'),
        
        # 页面浏览
        ('page_profile', '浏览个人主页'),
        ('page_my_resources', '浏览我的资源'),
        ('page_my_collections', '浏览我的收藏'),
        ('page_my_downloads', '浏览我的下载'),
        ('page_my_follows', '浏览我的关注'),
        ('page_my_history', '浏览浏览历史'),
        ('page_my_shares', '浏览分享历史'),
        ('page_my_earnings', '浏览收益统计'),
        ('page_profile_edit', '浏览账号设置'),
        ('page_ranking', '浏览排行榜'),
        ('page_notifications', '浏览消息中心'),
        ('view_notification', '查看消息通知'),
        ('delete_notification', '删除消息'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='用户'
    )
    resource = models.ForeignKey(
        'resources.Resource',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='资源'
    )
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name='行为类型'
    )
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='额外数据',
        help_text='如：{"position": 3, "stay_duration": 12, "search_query": "数学"}'
    )
    session_id = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        verbose_name='会话ID'
    )
    device_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name='设备ID'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP地址'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='行为时间',
        db_index=True
    )
    
    class Meta:
        db_table = 'recommendations_behavior'
        ordering = ['-created_at']
        verbose_name = '用户行为'
        verbose_name_plural = '用户行为'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['resource', 'action']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user or '游客'} {self.get_action_display()} {self.resource or ''}"