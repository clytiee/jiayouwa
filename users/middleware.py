from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class DailyLoginBonusMiddleware:
    """每天首次访问时发放登录奖励"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            today = timezone.now().date()
            if request.user.daily_login_date != today:
                try:
                    from transactions.services import OilService
                    request.user.daily_login_date = today
                    request.user.save(update_fields=['daily_login_date'])
                    OilService.add_oil(
                        request.user, 1, 'daily_login', '每日登录奖励'
                    )
                    logger.info(f'[每日奖励] {request.user.username} 获得 1 油滴')
                except Exception as e:
                    logger.error(f'[每日奖励] 发放失败: {e}')
        
        return self.get_response(request)