from .models import Notification
from transactions.models import OilTransaction
from django.db.models import Sum


def unread_notification_count(request):
    """全局注入未读消息数、最近消息列表和油滴增加数"""
    context = {
        'unread_count': 0,
        'recent_notifications': [],
        'oil_since_last_login': 0,
    }
    
    if request.user.is_authenticated:
        user = request.user
        
        # 消息通知
        unread_notifications = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).order_by('-created_at')
        
        unread_count = unread_notifications.count()
        recent_unread = unread_notifications[:5]
        
        # ✅ 上次登录以来的油滴增加数
        last_login = user.last_login
        oil_since_last_login = 0
        if last_login:
            oil_since_last_login = OilTransaction.objects.filter(
                user=user,
                amount__gt=0,
                created_at__gt=last_login
            ).aggregate(Sum('amount'))['amount__sum'] or 0
        else:
            oil_since_last_login = OilTransaction.objects.filter(
                user=user,
                amount__gt=0
            ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        context.update({
            'unread_count': unread_count,
            'recent_notifications': recent_unread,
            'oil_since_last_login': oil_since_last_login,
        })
    
    return context