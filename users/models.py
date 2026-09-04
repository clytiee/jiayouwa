from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    自定义用户模型
    使用用户名登录，邮箱用于验证和找回密码
    """
    # AbstractUser 已提供: username, email, password, is_active, date_joined, last_login
    
    # 自定义字段
    avatar = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="用户自定义头像URL，为空则显示默认青蛙头像"
    )
    
    oil_balance = models.IntegerField(default=0, help_text="油滴余额")
    
    level = models.IntegerField(default=1, help_text="成长等级")
    exp = models.IntegerField(default=0, help_text="当前等级经验值")
    level_title = models.CharField(max_length=50, blank=True, default="小蝌蚪", help_text="等级称号")
    
    has_used_free_trial = models.BooleanField(default=False, help_text="是否已使用首次免费下载")
    
    invited_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="邀请人"
    )
    
    daily_login_date = models.DateField(null=True, blank=True, help_text="最近一次登录日期（用于每日奖励去重）")
    
    is_banned = models.BooleanField(default=False, help_text="是否被封禁")
    
    class Meta:
        db_table = 'users_user'
        verbose_name = '用户'
        verbose_name_plural = '用户'
    
    def __str__(self):
        return self.username
    
    @property
    def display_avatar(self):
        """返回显示头像，如果没有自定义则返回默认青蛙SVG"""
        if self.avatar:
            return self.avatar
        return None  # 前端根据None显示默认青蛙
    
    @property
    def oil_display(self):
        """格式化显示油滴数"""
        return f"{self.oil_balance}"


class Follow(models.Model):
    """关注关系表"""
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following_set',
        verbose_name='关注者'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower_set',
        verbose_name='被关注者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='关注时间')
    
    class Meta:
        db_table = 'users_follow'
        unique_together = ['follower', 'following']
        verbose_name = '关注关系'
        verbose_name_plural = '关注关系'
    
    def __str__(self):
        return f"{self.follower.username} -> {self.following.username}"