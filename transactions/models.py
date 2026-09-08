from django.db import models
from django.conf import settings


class OilTransaction(models.Model):
    """油滴交易记录"""
    
    TYPE_CHOICES = (
        ('register_bonus', '注册奖励'),
        ('daily_login', '每日登录'),
        ('share_click', '分享点击'),
        ('share_register', '分享注册'),
        ('share_download', '分享下载'),
        ('upload_earning', '上传收益'),
        ('download_payment', '下载支付'),
        ('upvote_reward', '点赞奖励'),
        ('collect_reward', '收藏奖励'),
        ('comment_up_reward', '评论被顶'),
        ('admin_adjust', '管理员调整'),
        ('invite_reward', '邀请奖励'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户')
    amount = models.IntegerField(verbose_name='变动数量')
    balance_after = models.IntegerField(verbose_name='交易后余额')
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, verbose_name='交易类型')
    description = models.CharField(max_length=255, blank=True, verbose_name='描述')
    related_resource = models.ForeignKey('resources.Resource', null=True, blank=True,
                                         on_delete=models.SET_NULL, verbose_name='关联资源')
    related_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='related_transactions', verbose_name='关联用户')
    related_comment = models.ForeignKey('resources.Comment', null=True, blank=True,  # ✅ 新增 
                                        on_delete=models.SET_NULL, verbose_name='关联评论')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='交易时间')
    
    class Meta:
        db_table = 'transactions_oiltransaction'
        ordering = ['-created_at']
        verbose_name = '油滴交易'
        verbose_name_plural = '油滴交易'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.amount} ({self.get_type_display()})"