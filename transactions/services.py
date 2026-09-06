from django.db import transaction
from django.utils import timezone
from .models import OilTransaction
from users.models import User
from users.services import ExpService
import logging

logger = logging.getLogger(__name__)


class OilService:
    """油滴服务"""
    
    @staticmethod
    def add_oil(user, amount, trans_type, description='', related_resource=None, related_user=None):
        """增加油滴"""
        if amount <= 0:
            return False
        
        with transaction.atomic():
            user.oil_balance += amount
            user.save()
            
            OilTransaction.objects.create(
                user=user,
                amount=amount,
                balance_after=user.oil_balance,
                type=trans_type,
                description=description,
                related_resource=related_resource,
                related_user=related_user
            )
        
        # 同时增加经验值
        exp_amount = ExpService._get_exp_for_action(trans_type)  # ← 调用 ExpService 的方法
        if exp_amount > 0:
            ExpService.add_exp(user, exp_amount, trans_type)
        
        logger.info(f"用户 {user.username} 获得 {amount} 油滴，原因: {trans_type}")
        return True
    
    @staticmethod
    def deduct_oil(user, amount, trans_type, description='', related_resource=None, related_user=None):
        """扣除油滴"""
        if amount <= 0:
            return False
        
        if user.oil_balance < amount:
            return False
        
        with transaction.atomic():
            user.oil_balance -= amount
            user.save()
            
            OilTransaction.objects.create(
                user=user,
                amount=-amount,
                balance_after=user.oil_balance,
                type=trans_type,
                description=description,
                related_resource=related_resource,
                related_user=related_user
            )
        
        logger.info(f"用户 {user.username} 消耗 {amount} 油滴，原因: {trans_type}")
        return True
    
    @staticmethod
    def register_bonus(user):
        """注册奖励"""
        return OilService.add_oil(
            user, 10, 'register_bonus', '注册奖励'
        )
    
    @staticmethod
    def daily_login_bonus(user):
        """每日登录奖励"""
        today = timezone.now().date()
        if user.daily_login_date == today:
            return True
        
        user.daily_login_date = today
        user.save()
        
        return OilService.add_oil(
            user, 1, 'daily_login', '每日登录奖励'
        )
    
    @staticmethod
    def share_click_bonus(user, share):
        """分享点击奖励"""
        return OilService.add_oil(
            user, 1, 'share_click', f'分享点击奖励 ({share.share_id})',
            related_resource=share.resource
        )
    
    @staticmethod
    def share_register_bonus(user, share, new_user):
        """分享注册奖励"""
        return OilService.add_oil(
            user, 5, 'share_register', f'分享注册奖励 ({share.share_id})',
            related_resource=share.resource,
            related_user=new_user
        )
    
    @staticmethod
    def share_download_bonus(user, share, downloader):
        """分享下载奖励（每个分享链接限前10次）"""
        # 统计该分享链接已经奖励的下载次数
        from transactions.models import OilTransaction
        from django.db.models import Q
        
        reward_count = OilTransaction.objects.filter(
            Q(type='share_download') &
            Q(description__icontains=share.share_id) &
            Q(user=user)
        ).count()
        
        # 如果已达到10次，不再奖励
        if reward_count >= 10:
            return False
        
        return OilService.add_oil(
            user, 1, 'share_download', f'分享下载奖励 ({share.share_id})',
            related_resource=share.resource,
            related_user=downloader
        )
    
    @staticmethod
    def upload_earning(user, resource, amount):
        """上传者收益"""
        return OilService.add_oil(
            user, amount, 'upload_earning', f'资源《{resource.title}》被下载',
            related_resource=resource
        )
    
    @staticmethod
    def download_payment(user, resource, amount):
        """下载支付"""
        return OilService.deduct_oil(
            user, amount, 'download_payment', f'下载资源《{resource.title}》',
            related_resource=resource
        )

    @staticmethod
    def add_oil(user, amount, trans_type, description='', related_resource=None, related_user=None):
        """增加油滴"""
        if amount <= 0:
            return False
        
        with transaction.atomic():
            user.oil_balance += amount
            user.save()
            
            OilTransaction.objects.create(
                user=user,
                amount=amount,
                balance_after=user.oil_balance,
                type=trans_type,
                description=description,
                related_resource=related_resource,
                related_user=related_user
            )
        
        # 🆕 同时增加经验值
        exp_amount = ExpService._get_exp_for_action(trans_type)
        if exp_amount > 0:
            ExpService.add_exp(user, exp_amount, trans_type)
        
        logger.info(f"用户 {user.username} 获得 {amount} 油滴，原因: {trans_type}")
        return True
    
    @staticmethod
    def _get_exp_for_action(action_type):
        """根据行为类型获取经验值"""
        exp_map = {
            'register_bonus': 5,
            'daily_login': 2,
            'share_click': 1,
            'share_register': 3,
            'share_download': 2,
            'upload_earning': 10,  # 每次资源被下载
            'upvote_reward': 1,
            'collect_reward': 1,
            'comment_up_reward': 1,
        }
        return exp_map.get(action_type, 0)