from .models import Notification


def unread_notification_count(request):
    """全局注入未读消息数和最近消息列表"""
    if request.user.is_authenticated:
        # 获取所有未读消息，按时间倒序
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).order_by('-created_at')
        
        unread_count = unread_notifications.count()
        
        # 最近5条未读消息
        recent_unread = unread_notifications[:5]
        
        return {
            'unread_count': unread_count,
            'recent_notifications': recent_unread,
        }
    return {
        'unread_count': 0,
        'recent_notifications': [],
    }