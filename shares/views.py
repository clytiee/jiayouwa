from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import uuid
import logging

from resources.models import Resource
from .models import Share
from transactions.services import OilService

logger = logging.getLogger(__name__)


@login_required
@require_POST
def create_share(request):
    """
    创建分享链接
    """
    try:
        data = json.loads(request.body)
        resource_id = data.get('resource_id')
        channel = data.get('channel', '')  # 分享渠道：wechat/xiaohongshu/douyin等
        
        if not resource_id:
            return JsonResponse({'success': False, 'error': '资源ID不能为空'})
        
        resource = get_object_or_404(Resource, id=resource_id, status='published')
        
        # 生成唯一分享码
        share_id = f"s_{uuid.uuid4().hex[:8]}"
        
        # 创建分享记录
        share = Share.objects.create(
            share_id=share_id,
            sharer=request.user,
            resource=resource,
            channel=channel
        )
        
        # 构建分享链接
        share_url = request.build_absolute_uri(f'/s/{share_id}/')
        
        return JsonResponse({
            'success': True,
            'share_id': share_id,
            'share_url': share_url,
            'resource_title': resource.title,
            'resource_cover': resource.cover_images[0] if resource.cover_images else None,
            'message': '🎉 分享链接已生成！'
        })
        
    except Exception as e:
        logger.error(f"创建分享失败: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


def share_landing(request, share_id):
    """
    分享落地页
    处理点击追踪 + 注册追踪
    """
    share = get_object_or_404(Share, share_id=share_id)
    resource = share.resource
    
    # 增加点击计数（防刷：同一IP/设备24小时内只计1次）
    # 简化实现：每次点击都计数
    share.click_count += 1
    share.save()
    
    # 给分享者加油滴（点击奖励）
    if request.user.is_authenticated and request.user != share.sharer:
        # 如果登录用户点击，只计1次
        session_key = f'share_click_{share_id}'
        if not request.session.get(session_key):
            OilService.share_click_bonus(share.sharer, share)
            request.session[session_key] = True
    
    # 如果是登录用户访问，记录注册来源
    if request.user.is_authenticated and request.user != share.sharer:
        # 检查是否已经通过此链接注册过
        if request.user.invited_by is None:
            # 记录邀请关系
            request.user.invited_by = share.sharer
            request.user.save()
            # 给分享者注册奖励
            OilService.share_register_bonus(share.sharer, share, request.user)
    
    # 跳转到资源详情页（带分享来源参数）
    return redirect(f'/resource/{resource.id}/?from=share&share_id={share_id}')