from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import models
from django.utils import timezone
import json
import base64
import logging
from PIL import Image
from io import BytesIO

from .forms import ResourceUploadForm
from .models import Resource, Collect, Download, Comment, CommentVote
from transactions.services import OilService
from users.models import User, Follow
from recommendations.models import BrowseHistory
from .ai_service import AIService


logger = logging.getLogger(__name__)


# resources/views.py 中的 resource_upload 函数
from .tag_service import TagService

@login_required
def resource_upload(request):
    """资源发布页面"""
    if request.method == 'POST':
        form = ResourceUploadForm(request.POST)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploader = request.user
            resource.save()
            
            # 处理预览图
            images_data = request.POST.get('images_data', '')
            if images_data:
                processed_images = _process_images(images_data)
                if processed_images:
                    resource.cover_images = processed_images
                    resource.save()
            
            # ✅ 预设标签匹配（本地，零成本，即时生效）
            preset_tags = TagService.get_preset_tags(resource.title, resource.description)
            
            # 如果有预设标签，先保存（用户马上能看到）
            if preset_tags:
                resource.tags = preset_tags[:5]
                resource.ai_tags_generated = False  # 标记AI还未生成
                resource.save()
                logger.info(f'[预设标签] 资源 {resource.id} 匹配到: {preset_tags[:5]}')
            
            # 🆕 异步调用 AI 补充标签（不阻塞响应）
            import threading
            
            def generate_ai_tags():
                try:
                    logger.info(f'[AI标签] 资源 {resource.id} 开始生成...')
                    ai_result = AIService.generate_resource_tags(
                        resource.title, 
                        resource.description
                    )
                    logger.info(f'[AI标签] 资源 {resource.id} AI返回: {ai_result}')
                    
                    if ai_result and ai_result.get('tags'):
                        # 合并预设标签和AI标签
                        existing_tags = resource.tags or []
                        new_tags = ai_result.get('tags', [])
                        # 合并去重
                        merged = list(set(existing_tags + new_tags))[:5]
                        resource.tags = merged
                        resource.grade = ai_result.get('grade', '')
                        resource.resource_type = ai_result.get('resource_type', '')
                        resource.ai_tags_generated = True
                        resource.save()
                        logger.info(f'[AI标签] 资源 {resource.id} 最终标签: {merged}')
                except Exception as e:
                    logger.error(f'[AI标签] 资源 {resource.id} 失败: {e}')
            
            thread = threading.Thread(target=generate_ai_tags)
            thread.start()
            logger.info(f'[AI标签] 资源 {resource.id} 线程已启动')
            
            messages.success(request, f'🎉 资源《{resource.title}》发布成功！AI 正在自动生成补充标签，请稍后刷新查看。')
            return redirect('resources:detail', resource_id=resource.id)
        else:
            messages.error(request, '发布失败，请检查表单中的错误。')
    else:
        form = ResourceUploadForm()
    
    context = {
        'form': form,
        'max_price': settings.DEFAULT_SETTINGS.get('oil_price_max', 10),
        'min_price': settings.DEFAULT_SETTINGS.get('oil_price_min', 0),
    }
    return render(request, 'resources/resource_upload.html', context)

def _process_images(images_data):
    """
    处理前端传来的Base64图片数据
    返回压缩后的图片列表（Base64或存储路径）
    """
    processed = []
    try:
        data = json.loads(images_data)
        for idx, img_data in enumerate(data[:7]):  # 最多7张
            if img_data.startswith('data:image'):
                # 移除 data:image/xxx;base64, 前缀
                format, imgstr = img_data.split(';base64,')
                ext = format.split('/')[-1]
                image_data = base64.b64decode(imgstr)
                
                # 打开并压缩图片
                img = Image.open(BytesIO(image_data))
                
                # 转换为RGB（如果是RGBA）
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # 压缩到最大200KB
                quality = 85
                while True:
                    output = BytesIO()
                    img.save(output, format='JPEG', quality=quality, optimize=True)
                    if output.tell() <= 200 * 1024 or quality <= 10:
                        break
                    quality -= 5
                
                # 转为Base64存储（或可以存储到文件系统）
                compressed_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
                processed.append(f'data:image/jpeg;base64,{compressed_base64}')
                
    except Exception as e:
        logger.error(f"图片处理失败: {e}")
    
    return processed


@login_required
def resource_edit(request, resource_id):
    """编辑资源"""
    resource = get_object_or_404(Resource, id=resource_id, uploader=request.user)
    
    if request.method == 'POST':
        form = ResourceUploadForm(request.POST, instance=resource)
        if form.is_valid():
            resource = form.save()
            messages.success(request, f'✅ 资源《{resource.title}》更新成功！')
            return redirect('resources:detail', resource_id=resource.id)
    else:
        form = ResourceUploadForm(instance=resource)
    
    context = {
        'form': form,
        'resource': resource,
        'is_edit': True,
    }
    return render(request, 'resources/resource_upload.html', context)


@login_required
@require_POST
def resource_delete(request, resource_id):
    """删除资源"""
    resource = get_object_or_404(Resource, id=resource_id, uploader=request.user)
    title = resource.title
    resource.delete()
    messages.success(request, f'🗑️ 资源《{title}》已删除。')
    return redirect('users:my_resources')


# ========== 图片上传API（供前端Ajax使用） ==========

@login_required
@csrf_exempt
@require_POST
def upload_preview_image(request):
    """
    上传预览图API
    前端压缩后通过Ajax上传
    """
    try:
        data = json.loads(request.body)
        image_data = data.get('image', '')
        index = data.get('index', 0)
        
        if not image_data:
            return JsonResponse({'success': False, 'error': '图片数据为空'})
        
        # 处理图片并返回存储路径或Base64
        processed = _process_images(json.dumps([image_data]))
        
        if processed:
            return JsonResponse({
                'success': True,
                'url': processed[0],
                'index': index
            })
        else:
            return JsonResponse({'success': False, 'error': '图片处理失败'})
            
    except Exception as e:
        logger.error(f"上传预览图失败: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

# ========== 资源详情 ==========

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q, Count
from django.core.paginator import Paginator
import json
import logging

from .models import Resource, Collect, Download, Comment, CommentVote
from transactions.services import OilService
from users.models import Follow
from recommendations.models import BrowseHistory

logger = logging.getLogger(__name__)


def resource_detail(request, resource_id):
    """资源详情页"""
    resource = get_object_or_404(Resource, id=resource_id, status='published')
    user = request.user
    
    # 增加浏览量（使用update避免触发信号）
    Resource.objects.filter(id=resource_id).update(view_count=models.F('view_count') + 1)
    
    # 记录浏览历史（登录用户）
    if user.is_authenticated:
        BrowseHistory.objects.update_or_create(
            user=user,
            resource=resource,
            defaults={'viewed_at': timezone.now()}
        )
    
    # ===== 下载权限判断 =====
    is_uploader = user.is_authenticated and user.id == resource.uploader.id
    has_purchased = False
    if user.is_authenticated:
        has_purchased = Download.objects.filter(user=user, resource=resource).exists()

    # ===== 是否有提取码 =====
    has_extract_code = bool(resource.extract_code and resource.extract_code.strip())
    
    # ===== 下载权限判断 =====
    is_uploader = user.is_authenticated and user.id == resource.uploader.id
    has_purchased = False
    if user.is_authenticated:
        has_purchased = Download.objects.filter(user=user, resource=resource).exists()
    
    # 是否已付费（上传者自动视为已付费）
    can_see_extract = is_uploader or has_purchased or resource.price == 0
    
    # 游客免费下载判断
    can_download_free_trial = False
    if not user.is_authenticated:
        can_download_free_trial = not request.session.get('has_used_free_trial', False)
    else:
        if not has_purchased and not user.has_used_free_trial and not is_uploader:
            can_download_free_trial = True
    
    # ===== 收藏状态 =====
    is_collected = False
    if user.is_authenticated:
        is_collected = Collect.objects.filter(user=user, resource=resource).exists()
    
    # ===== 关注状态 =====
    is_following = False
    if user.is_authenticated and user.id != resource.uploader.id:
        is_following = Follow.objects.filter(follower=user, following=resource.uploader).exists()
    
    # ===== 用户评分 =====
    user_vote = None
    if user.is_authenticated:
        # 从CommentVote获取用户对资源的评分（简化：用资源本身的upvote/downvote记录）
        # 这里暂时从session或单独模型读取，简化处理
        pass
    
    # ===== 评论列表 =====
    comments = Comment.objects.filter(
        resource=resource,
        audit_status='visible',
        parent__isnull=True
    ).select_related('user').order_by('-created_at')
    
    # 评论分页
    comment_paginator = Paginator(comments, 20)
    comment_page = request.GET.get('comment_page', 1)
    comments_page = comment_paginator.get_page(comment_page)
    
    # 获取每个评论的顶踩数
    for comment in comments_page:
        comment.up_count = CommentVote.objects.filter(comment=comment, vote_type='up').count()
        comment.down_count = CommentVote.objects.filter(comment=comment, vote_type='down').count()
        if user.is_authenticated:
            comment.user_vote = CommentVote.objects.filter(
                comment=comment, 
                user=user
            ).first()
    
    # ===== 相关资源推荐 =====
    # 简单推荐：同标签的其他资源
    related_resources = []
    if resource.tags:
        related_resources = Resource.objects.filter(
            status='published',
            tags__overlap=resource.tags
        ).exclude(id=resource.id)[:6]
    
    context = {
        'resource': resource,
        'is_uploader': is_uploader,
        'has_purchased': has_purchased,
        'can_see_extract': can_see_extract,
        'can_download_free_trial': can_download_free_trial,
        'is_collected': is_collected,
        'is_following': is_following,
        'comments': comments_page,
        'related_resources': related_resources,
        'comment_count': comments.count(),
        'has_extract_code': has_extract_code,
    }
    
    return render(request, 'resources/resource_detail.html', context)


# ========== 下载处理 ==========

@login_required
@require_POST
def resource_download(request, resource_id):
    """处理资源下载 - 返回完整下载信息"""
    resource = get_object_or_404(Resource, id=resource_id, status='published')
    user = request.user
    
    # 上传者本人直接返回完整信息
    if user.id == resource.uploader.id:
        return JsonResponse({
            'success': True,
            'download_url': resource.download_url,
            'extract_code': resource.extract_code,
            'is_free': True,
            'can_see_extract': True,
        })
    
    # 检查是否已购买
    has_purchased = Download.objects.filter(user=user, resource=resource).exists()
    if has_purchased:
        return JsonResponse({
            'success': True,
            'download_url': resource.download_url,
            'extract_code': resource.extract_code,
            'is_free': False,
            'can_see_extract': True,
        })
    
    # 如果资源免费，直接返回
    if resource.price == 0:
        Download.objects.create(
            user=user,
            resource=resource,
            oil_paid=0,
            is_free_trial=False
        )
        return JsonResponse({
            'success': True,
            'download_url': resource.download_url,
            'extract_code': resource.extract_code,
            'is_free': True,
            'can_see_extract': True,
        })
    
    # 检查油滴是否足够
    if user.oil_balance < resource.price:
        return JsonResponse({
            'success': False,
            'error': f'油滴不足！需要 {resource.price} 油滴，当前仅有 {user.oil_balance} 油滴'
        })
    
    # 扣除油滴
    success = OilService.download_payment(user, resource, resource.price)
    if not success:
        return JsonResponse({
            'success': False,
            'error': '支付失败，请稍后重试'
        })
    
    # 记录下载
    Download.objects.create(
        user=user,
        resource=resource,
        oil_paid=resource.price,
        is_free_trial=False
    )
    
    # 给上传者加油滴
    OilService.upload_earning(resource.uploader, resource, resource.price)
    
    return JsonResponse({
        'success': True,
        'download_url': resource.download_url,
        'extract_code': resource.extract_code,
        'is_free': False,
        'oil_paid': resource.price,
        'can_see_extract': True,
    })


# ========== 游客免费下载 ==========

def free_download(request, resource_id):
    """游客免费下载"""
    resource = get_object_or_404(Resource, id=resource_id, status='published')
    
    # 检查是否已用过免费下载
    if request.session.get('has_used_free_trial', False):
        messages.warning(request, '您已经使用过免费下载机会，请注册登录后下载更多资源')
        return redirect('users:register')
    
    # 记录免费下载（不存入数据库，仅session标记）
    request.session['has_used_free_trial'] = True
    
    # 记录下载（游客不关联用户）
    # 这里可以通过session_id记录，暂不实现
    
    return JsonResponse({
        'success': True,
        'download_url': resource.download_url,
        'is_free': True,
        'message': '🎉 首次免费下载成功！注册登录后可下载更多资源'
    })

@login_required
@require_POST
def report_invalid(request, resource_id):
    """报告资源链接失效"""
    resource = get_object_or_404(Resource, id=resource_id)
    
    # 记录报告（可以创建 Report 模型，简单起见先发通知）
    from notifications.models import Notification
    
    Notification.objects.create(
        recipient=resource.uploader,
        sender=request.user,
        title=f'⚠️ 资源链接失效报告',
        content=f'用户 {request.user.first_name|default:request.user.username} 报告资源《{resource.title}》的下载链接可能已失效，请核查。',
        message_type='system',
        related_resource=resource
    )
    
    # 同时给管理员发通知（如果有管理员账号）
    from users.models import User
    admin = User.objects.filter(is_superuser=True).first()
    if admin:
        Notification.objects.create(
            recipient=admin,
            sender=request.user,
            title=f'⚠️ 资源链接失效报告',
            content=f'用户 {request.user.first_name|default:request.user.username} 报告资源《{resource.title}》链接失效，请核查。',
            message_type='system',
            related_resource=resource
        )
    
    return JsonResponse({'success': True})

# ========== 收藏切换 ==========

@login_required
@require_POST
def toggle_collect(request, resource_id):
    """切换收藏状态"""
    resource = get_object_or_404(Resource, id=resource_id)
    
    collect, created = Collect.objects.get_or_create(
        user=request.user,
        resource=resource
    )
    
    if not created:
        collect.delete()
        Resource.objects.filter(id=resource_id).update(collect_count=models.F('collect_count') - 1)
        return JsonResponse({'collected': False, 'count': resource.collect_count - 1})
    else:
        Resource.objects.filter(id=resource_id).update(collect_count=models.F('collect_count') + 1)
        
        # ✅ 只有收藏的不是自己发布的资源，才给油滴奖励
        if resource.uploader != request.user:
            OilService.add_oil(
                request.user, 
                1, 
                'collect_reward', 
                f'收藏了资源《{resource.title}》'
            )
        
        return JsonResponse({'collected': True, 'count': resource.collect_count + 1})


# ========== 关注切换 ==========

@login_required
@require_POST
def toggle_follow(request, user_id):
    """切换关注状态"""
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user == request.user:
        return JsonResponse({'error': '不能关注自己'}, status=400)
    
    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target_user
    )
    
    if not created:
        follow.delete()
        return JsonResponse({'following': False})
    else:
        return JsonResponse({'following': True})


# ========== 评分 ==========

@login_required
@require_POST
def rate_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    vote_type = request.POST.get('vote_type', 'up')
    
    if vote_type not in ['up', 'down']:
        return JsonResponse({'error': '无效的评分类型'}, status=400)
    
    session_key = f'rated_{resource_id}_{request.user.id}'
    if request.session.get(session_key):
        return JsonResponse({'error': '您已经评过分了'}, status=400)
    
    # 更新计数
    if vote_type == 'up':
        resource.upvote_count += 1
    else:
        resource.downvote_count += 1
    
    # 计算评分（范围 -5 到 5）
    total_votes = resource.upvote_count + resource.downvote_count
    if total_votes > 0:
        # 公式：(赞 - 踩) / 总数 × 5
        resource.avg_rating = (resource.upvote_count - resource.downvote_count) / total_votes * 5
    else:
        resource.avg_rating = 0
    
    resource.save()
    request.session[session_key] = vote_type
    
    return JsonResponse({
        'success': True,
        'up_count': resource.upvote_count,
        'down_count': resource.downvote_count,
        'avg_rating': resource.avg_rating
    })


# ========== 评论 ==========

@login_required
@require_POST
def add_comment(request, resource_id):
    """添加评论（AJAX）"""
    resource = get_object_or_404(Resource, id=resource_id)
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')
    
    if not content:
        return JsonResponse({'success': False, 'error': '评论内容不能为空'})
    
    if len(content) > 1000:
        return JsonResponse({'success': False, 'error': '评论内容不能超过1000字'})
    
    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, id=parent_id)
    
    comment = Comment.objects.create(
        user=request.user,
        resource=resource,
        parent=parent,
        content=content,
        audit_status='visible'
    )
    
    # 发送通知
    if resource.uploader != request.user:
        from notifications.models import Notification
        username = request.user.first_name or request.user.username  # ← 修复这里
        Notification.objects.create(
            recipient=resource.uploader,
            sender=request.user,
            title=f'新评论：{resource.title}',
            content=f'{username} 评论了你的资源：{content[:50]}...',
            message_type='comment',
            related_resource=resource
        )
    
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'username': request.user.first_name or request.user.username,
            'level': request.user.level,
            'content': comment.content,
            'created_at': comment.created_at.isoformat(),
        }
    })


@login_required
@require_POST
def vote_comment(request, comment_id):
    """评论顶/踩"""
    comment = get_object_or_404(Comment, id=comment_id)
    vote_type = request.POST.get('vote_type', 'up')
    
    if vote_type not in ['up', 'down']:
        return JsonResponse({'error': '无效的投票类型'}, status=400)
    
    # 检查是否已投票
    existing = CommentVote.objects.filter(user=request.user, comment=comment).first()
    
    if existing:
        if existing.vote_type == vote_type:
            # 取消投票
            existing.delete()
            if vote_type == 'up':
                comment.upvote_count -= 1
            else:
                comment.downvote_count -= 1
            comment.save()
            return JsonResponse({
                'action': 'removed',
                'up_count': comment.upvote_count,
                'down_count': comment.downvote_count
            })
        else:
            # 切换投票
            existing.vote_type = vote_type
            existing.save()
            if vote_type == 'up':
                comment.upvote_count += 1
                comment.downvote_count -= 1
            else:
                comment.downvote_count += 1
                comment.upvote_count -= 1
            comment.save()
            return JsonResponse({
                'action': 'switched',
                'up_count': comment.upvote_count,
                'down_count': comment.downvote_count
            })
    else:
        # 新增投票
        CommentVote.objects.create(
            user=request.user,
            comment=comment,
            vote_type=vote_type
        )
        if vote_type == 'up':
            comment.upvote_count += 1
        else:
            comment.downvote_count += 1
        comment.save()
        
        # 评论被顶奖励
        if vote_type == 'up' and comment.user != request.user:
            OilService.add_oil(
                comment.user, 1, 'comment_up_reward', 
                f'你的评论被 {request.user.first_name} 顶了'
            )
        
        return JsonResponse({
            'action': 'added',
            'up_count': comment.upvote_count,
            'down_count': comment.downvote_count
        })
