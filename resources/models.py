from django.db import models
from django.conf import settings
from django.utils import timezone


class Resource(models.Model):
    """资源模型"""
    
    STATUS_CHOICES = (
        ('published', '已发布'),
        ('pending', '待审核'),
        ('rejected', '不通过'),
        ('expired', '已失效'),
    )
    
    GRADE_CHOICES = (
        ('小学', '小学'),
        ('初中', '初中'),
        ('高中', '高中'),
    )
    
    TYPE_CHOICES = (
        ('视频', '视频'),
        ('文档', '文档'),
        ('网站', '网站'),
        ('APP', 'APP'),
        ('教具', '教具'),
        ('其他', '其他'),
    )
    
    # 基本信息
    title = models.CharField(max_length=200, verbose_name='标题')
    description = models.TextField(blank=True, verbose_name='描述')
    
    # 分类信息（AI自动生成，用户可修改）
    tags = models.JSONField(default=list, blank=True, verbose_name='标签')
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES, blank=True, verbose_name='适用年级')
    resource_type = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=True, verbose_name='资源类型')
    
    # 媒体
    cover_images = models.JSONField(default=list, blank=True, verbose_name='预览图列表')
    download_url = models.URLField(
        max_length=500, 
        verbose_name='下载链接',
        blank=True,
        null=True
    )
    extract_code = models.CharField(
        max_length=50, 
        blank=True, 
        default='',
        verbose_name='提取码'
    )
    
    # 油滴
    price = models.IntegerField(default=0, verbose_name='油滴价格')
    
    # 上传者
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='上传者')
    
    # 状态
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published', verbose_name='状态')
    
    # AI审核
    ai_risk_score = models.IntegerField(default=0, verbose_name='AI风险评分')
    ai_risk_reason = models.TextField(blank=True, verbose_name='AI风险原因')
    
    # 审核信息
    audited_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    audited_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, 
                                   on_delete=models.SET_NULL, related_name='audited_resources', verbose_name='审核人')
    reject_reason = models.TextField(blank=True, verbose_name='不通过原因')
    
    # 统计缓存
    view_count = models.IntegerField(default=0, verbose_name='浏览次数')
    download_count = models.IntegerField(default=0, verbose_name='下载次数')
    collect_count = models.IntegerField(default=0, verbose_name='收藏次数')
    upvote_count = models.IntegerField(default=0, verbose_name='点赞数')
    downvote_count = models.IntegerField(default=0, verbose_name='踩数')
    avg_rating = models.FloatField(default=0.0, verbose_name='平均评分')
    
    # AI标记
    ai_tags_generated = models.BooleanField(default=False, verbose_name='AI标签已生成')
    
    # 时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'resources_resource'
        ordering = ['-created_at']
        verbose_name = '资源'
        verbose_name_plural = '资源'
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['uploader', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def cover_image(self):
        """获取第一张预览图"""
        if self.cover_images and len(self.cover_images) > 0:
            return self.cover_images[0]
        return None


class Collect(models.Model):
    """收藏模型"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, verbose_name='资源')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='收藏时间')
    is_active = models.BooleanField(default=True, verbose_name='是否收藏中')
    has_rewarded = models.BooleanField(default=False, verbose_name='是否已给发布者奖励')
    
    class Meta:
        db_table = 'resources_collect'
        unique_together = ['user', 'resource']
        ordering = ['-created_at']
        verbose_name = '收藏'
        verbose_name_plural = '收藏'
    
    def __str__(self):
        return f"{self.user.username} 收藏了 {self.resource.title}"


class Download(models.Model):
    """下载记录模型"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, verbose_name='资源')
    downloaded_at = models.DateTimeField(auto_now_add=True, verbose_name='首次下载时间')
    last_downloaded_at = models.DateTimeField(auto_now=True, verbose_name='最近下载时间')
    is_free_trial = models.BooleanField(default=False, verbose_name='是否免费试用')
    oil_paid = models.IntegerField(default=0, verbose_name='支付油滴数')
    
    class Meta:
        db_table = 'resources_download'
        unique_together = ['user', 'resource']
        ordering = ['-last_downloaded_at']
        verbose_name = '下载记录'
        verbose_name_plural = '下载记录'
    
    def __str__(self):
        return f"{self.user.username} 下载了 {self.resource.title}"


class Comment(models.Model):
    """评论模型"""
    
    AUDIT_STATUS_CHOICES = (
        ('visible', '已显示'),
        ('hidden', '待审核'),
        ('rejected', '不通过'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='评论者')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, verbose_name='资源')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, verbose_name='父评论')
    content = models.TextField(verbose_name='评论内容')
    
    upvote_count = models.IntegerField(default=0, verbose_name='顶数')
    downvote_count = models.IntegerField(default=0, verbose_name='踩数')
    
    audit_status = models.CharField(max_length=20, choices=AUDIT_STATUS_CHOICES, default='visible', verbose_name='审核状态')
    ai_risk_score = models.IntegerField(default=0, verbose_name='AI风险评分')
    audited_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    audited_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='audited_comments', verbose_name='审核人')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='评论时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'resources_comment'
        ordering = ['created_at']
        verbose_name = '评论'
        verbose_name_plural = '评论'
    
    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}..."


class CommentVote(models.Model):
    """评论投票（顶/踩）"""
    
    VOTE_CHOICES = (
        ('up', '顶'),
        ('down', '踩'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='评论')
    vote_type = models.CharField(max_length=10, choices=VOTE_CHOICES, verbose_name='投票类型')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='投票时间')
    
    class Meta:
        db_table = 'resources_commentvote'
        unique_together = ['user', 'comment']
        verbose_name = '评论投票'
        verbose_name_plural = '评论投票'
    
    def __str__(self):
        return f"{self.user.username} {self.vote_type} 了评论 {self.comment.id}"

from django.db import models
from django.utils import timezone
from datetime import timedelta


class GlobalFreeQuota(models.Model):
    """全局免费下载额度池"""
    is_available = models.BooleanField(default=True, verbose_name='当前是否可用')
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='上次使用时间')
    
    class Meta:
        db_table = 'core_global_free_quota'
        verbose_name = '全局免费额度'
        verbose_name_plural = '全局免费额度'
    
    @classmethod
    def get_quota(cls):
        """获取唯一实例"""
        obj, created = cls.objects.get_or_create(id=1)
        return obj
    
    @property
    def can_use(self):
        """当前是否可用"""
        if self.is_available:
            return True
        # 检查是否已过冷却时间（1小时）
        cooldown = timedelta(hours=settings.FREE_QUOTA_COOLDOWN_HOURS)
        if self.used_at:
            elapsed = timezone.now() - self.used_at
            if elapsed >= cooldown:
                # 冷却结束，自动释放
                self.is_available = True
                self.save()
                return True
        return False
    
    def consume(self):
        """消耗额度"""
        if not self.can_use:
            return False
        self.is_available = False
        self.used_at = timezone.now()
        self.save()
        return True
    
    @property
    def next_available_time(self):
        """下次可用时间"""
        if self.is_available:
            return None
        if self.used_at:
            return self.used_at + timedelta(hours=1)
        return None
