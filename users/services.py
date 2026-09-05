from django.conf import settings
from .models import User


class ExpService:
    """经验值服务"""
    
    @staticmethod
    def get_level_config(level):
        """获取等级配置"""
        for lv in settings.LEVELS:
            if lv['level'] == level:
                return lv
        return None
    
    @staticmethod
    def get_next_level(level):
        """获取下一级配置"""
        for lv in settings.LEVELS:
            if lv['level'] == level + 1:
                return lv
        return None
    
    @staticmethod
    def get_level_by_exp(exp):
        """根据经验值计算当前等级"""
        current_level = 1
        for lv in settings.LEVELS:
            if exp >= lv['exp_required']:
                current_level = lv['level']
            else:
                break
        return current_level
    
    @staticmethod
    def get_level_title(level):
        """获取等级称号"""
        config = ExpService.get_level_config(level)
        return config['title'] if config else '小蝌蚪'
    
    @staticmethod
    def get_exp_progress(user):
        """获取经验值进度（当前等级 → 下一级）"""
        current_level = user.level
        current_exp = user.exp
        
        # 当前等级所需经验
        current_config = ExpService.get_level_config(current_level)
        if not current_config:
            return 0, 0, 100
        
        current_required = current_config['exp_required']
        
        # 下一级所需经验
        next_config = ExpService.get_next_level(current_level)
        if next_config:
            next_required = next_config['exp_required']
            progress = (current_exp - current_required) / (next_required - current_required) * 100
            progress = max(0, min(100, progress))
            return current_required, next_required, progress
        else:
            # 已满级
            return current_required, current_required, 100
    
    @staticmethod
    def add_exp(user, amount, source='', related_object=None):
        """增加经验值"""
        if amount <= 0:
            return
        
        user.exp += amount
        
        # 检查是否升级
        new_level = ExpService.get_level_by_exp(user.exp)
        old_level = user.level
        
        if new_level > old_level:
            user.level = new_level
            user.level_title = ExpService.get_level_title(new_level)
            # 触发升级通知
            ExpService._notify_level_up(user, old_level, new_level)
        
        user.save()
        return new_level > old_level
    
    @staticmethod
    def _notify_level_up(user, old_level, new_level):
        """发送升级通知"""
        from notifications.models import Notification
        
        old_title = ExpService.get_level_title(old_level)
        new_title = ExpService.get_level_title(new_level)
        
        Notification.objects.create(
            recipient=user,
            title=f'🎉 升级啦！{old_title} → {new_title}',
            content=f'恭喜你从「{old_title}」升级到「{new_title}」！继续加油，学习路上一起进步！🐸',
            message_type='system'
        )