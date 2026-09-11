import logging
from .models import Behavior

logger = logging.getLogger(__name__)


class BehaviorService:
    """行为记录服务（未来可替换为 Redis/消息队列）"""
    
    @staticmethod
    def track(user, action, resource=None, extra_data=None, request=None):
        """
        记录用户行为
        
        参数：
        - user: 用户对象（游客为 None）
        - action: 行为类型
        - resource: 资源对象（可选）
        - extra_data: 额外数据字典（可选）
        - request: HTTP 请求对象（用于获取 session_id、IP 等）
        """
        try:
            data = {
                'user': user if user and user.is_authenticated else None,
                'resource': resource,
                'action': action,
                'extra_data': extra_data or {},
            }
            
            if request:
                data['session_id'] = request.session.session_key
                data['ip_address'] = BehaviorService._get_client_ip(request)
                data['device_id'] = request.COOKIES.get('device_id', '') or request.META.get('HTTP_X_DEVICE_ID', '')
            
            Behavior.objects.create(**data)
            logger.debug(f'[行为] {user or "游客"} {action} {resource or ""}')
            return True
        except Exception as e:
            logger.error(f'[行为] 记录失败: {e}')
            return False
    
    @staticmethod
    def _get_client_ip(request):
        """获取客户端 IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip