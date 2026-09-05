from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Sum, Q
from django.core.paginator import Paginator
import logging

from .forms import RegisterForm, LoginForm
from .models import User, Follow
from resources.models import Resource, Collect, Download, Comment
from recommendations.models import BrowseHistory
from transactions.models import OilTransaction
from transactions.services import OilService
from shares.models import Share

logger = logging.getLogger(__name__)


def register_view(request):
    """用户注册"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            
            # 生成激活邮件
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            activation_link = request.build_absolute_uri(
                f'/activate/{uid}/{token}/'
            )
            
            send_mail(
                subject='激活你的加油哇账号',
                message=f'欢迎加入加油哇！请点击以下链接激活你的账号：\n\n{activation_link}\n\n学习路上，一起加油哇！🐸',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            messages.success(request, '注册成功！请查收邮件激活你的账号。')
            return redirect('users:login')
    else:
        form = RegisterForm()
    
    return render(request, 'users/register.html', {'form': form})


def activate_view(request, uidb64, token):
    """邮箱激活"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        
        # 赠送注册油滴
        OilService.register_bonus(user)
        
        # 处理邀请码
        invite_code = request.GET.get('invite')
        if invite_code:
            try:
                share = Share.objects.get(share_id=invite_code)
                if share.sharer != user:
                    share.register_count += 1
                    share.save()
                    OilService.share_register_bonus(share.sharer, share, user)
            except Share.DoesNotExist:
                pass
        
        user.save()
        login(request, user)
        messages.success(request, '账号激活成功！欢迎加入加油哇！🐸')
        return redirect('index')
    else:
        messages.error(request, '激活链接无效或已过期')
        return redirect('users:login')


def login_view(request):
    """用户登录"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember = form.cleaned_data.get('remember_me', False)
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                
                OilService.daily_login_bonus(user)
                
                if not remember:
                    request.session.set_expiry(0)
                
                messages.success(request, f'欢迎回来，{user.username}！🐸')
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
        else:
            messages.error(request, '用户名或密码错误')
    else:
        form = LoginForm()
    
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """用户登出"""
    logout(request)
    messages.info(request, '已成功登出')
    return redirect('index')


@login_required
def profile_view(request):
    """用户个人主页"""
    user = request.user
    
    # 统计数据
    resource_count = Resource.objects.filter(uploader=user, status='published').count()
    collect_count = Collect.objects.filter(user=user).count()
    download_count = Download.objects.filter(user=user).count()
    follower_count = Follow.objects.filter(following=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    
    # ===== 最近动态（合并多种行为） =====
    from itertools import chain
    from django.utils import timezone
    
    activities = []
    
    # 1. 发布资源
    for r in Resource.objects.filter(uploader=user, status='published').order_by('-created_at')[:5]:
        activities.append({
            'icon': '📤',
            'text': '发布了资源',
            'resource': r,
            'time': r.created_at,
        })
    
    # 2. 收藏资源
    for c in Collect.objects.filter(user=user).order_by('-created_at')[:5]:
        activities.append({
            'icon': '❤️',
            'text': '收藏了资源',
            'resource': c.resource,
            'time': c.created_at,
        })
    
    # 3. 下载资源
    for d in Download.objects.filter(user=user).order_by('-downloaded_at')[:5]:
        activities.append({
            'icon': '📥',
            'text': '下载了资源',
            'resource': d.resource,
            'time': d.downloaded_at,
        })
    
    # 4. 评论
    for c in Comment.objects.filter(user=user).order_by('-created_at')[:5]:
        activities.append({
            'icon': '💬',
            'text': '评论了资源',
            'resource': c.resource,
            'time': c.created_at,
        })
    
    # 按时间排序，取最近10条
    activities.sort(key=lambda x: x['time'], reverse=True)
    recent_activities = activities[:10]
    
    context = {
        'user': user,
        'resource_count': resource_count,
        'collect_count': collect_count,
        'download_count': download_count,
        'follower_count': follower_count,
        'following_count': following_count,
        'recent_activities': recent_activities,
    }
    return render(request, 'users/profile.html', context)


@login_required
def profile_edit_view(request):
    """编辑个人资料"""
    user = request.user
    
    if request.method == 'POST':
        # 修改昵称
        first_name = request.POST.get('first_name', '').strip()
        if first_name:
            user.first_name = first_name
            user.save()
            messages.success(request, '✅ 昵称已更新！')
        else:
            messages.error(request, '❌ 昵称不能为空')
        
        # 修改密码
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if old_password and new_password1 and new_password2:
            if not user.check_password(old_password):
                messages.error(request, '❌ 当前密码错误')
            elif new_password1 != new_password2:
                messages.error(request, '❌ 两次输入的新密码不一致')
            elif len(new_password1) < 8:
                messages.error(request, '❌ 密码至少8位')
            else:
                user.set_password(new_password1)
                user.save()
                # 修改密码后重新登录
                from django.contrib.auth import login
                login(request, user)
                messages.success(request, '✅ 密码已更新，请重新登录')
                return redirect('users:profile_edit')
        
        return redirect('users:profile_edit')
    
    return render(request, 'users/profile_edit.html')


@login_required
def my_resources_view(request):
    """我的资源列表"""
    resources = Resource.objects.filter(uploader=request.user).order_by('-created_at')
    paginator = Paginator(resources, 20)
    page = request.GET.get('page', 1)
    resources_page = paginator.get_page(page)
    return render(request, 'users/my_resources.html', {'resources': resources_page})


@login_required
def my_collections_view(request):
    """我的收藏"""
    collections = Collect.objects.filter(user=request.user).select_related('resource').order_by('-created_at')
    paginator = Paginator(collections, 20)
    page = request.GET.get('page', 1)
    collections_page = paginator.get_page(page)
    return render(request, 'users/my_collections.html', {'collections': collections_page})


@login_required
def my_downloads_view(request):
    """我的下载"""
    downloads = Download.objects.filter(user=request.user).select_related('resource').order_by('-last_downloaded_at')
    paginator = Paginator(downloads, 20)
    page = request.GET.get('page', 1)
    downloads_page = paginator.get_page(page)
    return render(request, 'users/my_downloads.html', {'downloads': downloads_page})


@login_required
def my_follows_view(request):
    """我的关注"""
    follows = Follow.objects.filter(follower=request.user).select_related('following').order_by('-created_at')
    paginator = Paginator(follows, 20)
    page = request.GET.get('page', 1)
    follows_page = paginator.get_page(page)
    return render(request, 'users/my_follows.html', {'follows': follows_page})


@login_required
def my_history_view(request):
    """浏览历史"""
    history = BrowseHistory.objects.filter(user=request.user).select_related('resource').order_by('-viewed_at')
    paginator = Paginator(history, 20)
    page = request.GET.get('page', 1)
    history_page = paginator.get_page(page)
    return render(request, 'users/my_history.html', {'history': history_page})


@login_required
def clear_history_view(request):
    """清空浏览历史"""
    if request.method == 'POST':
        BrowseHistory.objects.filter(user=request.user).delete()
        messages.success(request, '浏览历史已清空')
    return redirect('users:my_history')


@login_required
def my_shares_view(request):
    """分享历史"""
    shares = Share.objects.filter(sharer=request.user).order_by('-created_at')
    paginator = Paginator(shares, 20)
    page = request.GET.get('page', 1)
    shares_page = paginator.get_page(page)
    return render(request, 'users/my_shares.html', {'shares': shares_page})


@login_required
def my_earnings_view(request):
    """收益统计"""
    transactions = OilTransaction.objects.filter(user=request.user).order_by('-created_at')
    
    total_income = OilTransaction.objects.filter(
        user=request.user,
        amount__gt=0
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_expense = OilTransaction.objects.filter(
        user=request.user,
        amount__lt=0
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    income_by_type = OilTransaction.objects.filter(
        user=request.user,
        amount__gt=0
    ).values('type').annotate(total=Sum('amount')).order_by('-total')
    
    paginator = Paginator(transactions, 30)
    page = request.GET.get('page', 1)
    transactions_page = paginator.get_page(page)
    
    context = {
        'transactions': transactions_page,
        'total_income': total_income,
        'total_expense': abs(total_expense),
        'balance': request.user.oil_balance,
        'income_by_type': income_by_type,
    }
    return render(request, 'users/my_earnings.html', {'transactions': transactions_page})