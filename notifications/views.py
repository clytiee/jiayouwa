from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Notification
from recommendations.services import BehaviorService

@login_required
def notification_list(request):
    """消息中心列表"""
    # ✅ 记录进入消息中心
    BehaviorService.track(
        user=request.user,
        action='page_notifications',
        request=request
    )
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # 统计未读数量
    unread_count = notifications.filter(is_read=False).count()
    
    paginator = Paginator(notifications, 20)
    page = request.GET.get('page', 1)
    notifications_page = paginator.get_page(page)
    
    context = {
        'notifications': notifications_page,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/list.html', context)


@login_required
@require_POST
def mark_read(request, notification_id):
    """标记单条消息为已读"""
    # ✅ 记录查看消息
    BehaviorService.track(
        user=request.user,
        action='view_notification',
        extra_data={'notification_id': notification_id},
        request=request
    )
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def mark_all_read(request):
    """标记所有消息为已读"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
@require_POST
def delete_notification(request, notification_id):
    """删除单条消息"""
    BehaviorService.track(
        user=request.user,
        action='delete_notification',
        extra_data={'notification_id': notification_id},
        request=request
    )
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.delete()
    return JsonResponse({'success': True})
    # ✅ 记录删除消息行为
