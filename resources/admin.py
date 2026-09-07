from django.contrib import admin
from django.urls import path  # ← 添加这行
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.html import format_html
from .models import Resource, Collect, Download, Comment, CommentVote
from .vector_search import VectorSearch

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'title_preview', 'uploader', 'grade', 'price', 'status', 'view_count', 'created_at']
    list_filter = ['status', 'grade', 'resource_type', 'created_at']
    search_fields = ['title', 'description', 'uploader__username', 'uploader__email']
    readonly_fields = ['view_count', 'download_count', 'collect_count', 'upvote_count', 'downvote_count', 'avg_rating', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'uploader', 'price')
        }),
        ('分类信息', {
            'fields': ('tags', 'grade', 'resource_type')
        }),
        ('文件信息', {
            'fields': ('cover_images', 'download_url')
        }),
        ('状态审核', {
            'fields': ('status', 'ai_risk_score', 'ai_risk_reason', 'reject_reason')
        }),
        ('统计数据', {
            'fields': ('view_count', 'download_count', 'collect_count', 'upvote_count', 'downvote_count', 'avg_rating')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def title_preview(self, obj):
        """标题预览"""
        if len(obj.title) > 30:
            return obj.title[:30] + '...'
        return obj.title
    title_preview.short_description = '标题'
    
    actions = ['approve_resources', 'reject_resources', 'mark_expired']
    
    def approve_resources(self, request, queryset):
        """批量审核通过"""
        count = queryset.update(status='published')
        self.message_user(request, f'已通过 {count} 个资源的审核')
    approve_resources.short_description = '审核通过所选资源'
    
    def reject_resources(self, request, queryset):
        """批量审核不通过"""
        count = queryset.update(status='rejected')
        self.message_user(request, f'已驳回 {count} 个资源')
    reject_resources.short_description = '审核不通过所选资源'
    
    def mark_expired(self, request, queryset):
        """批量标记失效"""
        count = queryset.update(status='expired')
        self.message_user(request, f'已标记 {count} 个资源为失效')
    mark_expired.short_description = '标记为失效'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('rebuild-index/', self.admin_site.admin_view(self.rebuild_index), name='rebuild_index'),
        ]
        return custom_urls + urls
    
    def rebuild_index(self, request):
        """重建向量索引"""
        try:
            count = VectorSearch.rebuild_index()
            messages.success(request, f'✅ 向量索引重建成功！')
        except Exception as e:
            messages.error(request, f'❌ 重建失败: {e}')
        return redirect('admin:resources_resource_changelist')

    def changelist_view(self, request, extra_context=None):
        """在列表页添加重建按钮"""
        extra_context = extra_context or {}
        extra_context['rebuild_index_url'] = 'rebuild-index/'
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(Collect)
class CollectAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource', 'created_at']
    search_fields = ['user__username', 'resource__title']
    list_filter = ['created_at']


@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource', 'downloaded_at', 'last_downloaded_at', 'is_free_trial', 'oil_paid']
    search_fields = ['user__username', 'resource__title']
    list_filter = ['is_free_trial', 'downloaded_at']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource', 'content_preview', 'audit_status', 'ai_risk_score', 'created_at']
    list_filter = ['audit_status', 'created_at']
    search_fields = ['user__username', 'resource__title', 'content']
    actions = ['approve_comments', 'reject_comments']
    
    def content_preview(self, obj):
        if len(obj.content) > 30:
            return obj.content[:30] + '...'
        return obj.content
    content_preview.short_description = '评论内容'
    
    def approve_comments(self, request, queryset):
        count = queryset.update(audit_status='visible')
        self.message_user(request, f'已通过 {count} 条评论')
    approve_comments.short_description = '审核通过所选评论'
    
    def reject_comments(self, request, queryset):
        count = queryset.update(audit_status='rejected')
        self.message_user(request, f'已驳回 {count} 条评论')
    reject_comments.short_description = '审核不通过所选评论'


@admin.register(CommentVote)
class CommentVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']