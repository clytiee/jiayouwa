import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from resources.models import Resource
from .services import BehaviorService
from .models import Behavior

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def track_behavior(request):
    """
    行为埋点 API
    接收前端发送的行为数据
    """
    try:
        data = json.loads(request.body)
        action = data.get('action')
        resource_id = data.get('resource_id')
        extra_data = data.get('extra_data', {})
        
        if not action:
            return JsonResponse({'success': False, 'error': '缺少 action 参数'})
        
        # 验证 action 合法性
        valid_actions = [a[0] for a in Behavior.ACTION_CHOICES]
        if action not in valid_actions:
            return JsonResponse({'success': False, 'error': '无效的 action'})
        
        # 获取资源
        resource = None
        if resource_id:
            try:
                resource = Resource.objects.get(id=resource_id)
            except Resource.DoesNotExist:
                pass
        
        # 记录行为
        BehaviorService.track(
            user=request.user,
            action=action,
            resource=resource,
            extra_data=extra_data,
            request=request
        )
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '无效的 JSON'})
    except Exception as e:
        logger.error(f'[行为API] 失败: {e}')
        return JsonResponse({'success': False, 'error': str(e)})