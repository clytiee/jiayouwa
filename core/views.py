from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from django.http import HttpResponse
from resources.models import Resource
from users.models import User


def home_view(request):
    view_mode = request.GET.get('mode')
    if view_mode in ['list', 'card']:
        request.session['view_mode'] = view_mode
    else:
        view_mode = request.session.get('view_mode', 'list')
    
    resources = Resource.objects.filter(status='published').order_by('-created_at')
    
    paginator = Paginator(resources, 9)
    page = request.GET.get('page', 1)
    resources_page = paginator.get_page(page)
    
    context = {
        'resources': resources_page,  # ← 确保这里是 resources_page，不是 resources
        'view_mode': view_mode,
    }
    
    if request.headers.get('HX-Request') == 'true':
        return render(request, 'partials/resource_list.html', context)
    print(f"page: {page}, 本页数量: {len(resources_page)}, 总资源数: {resources.count()}")
    return render(request, 'index.html', context)


def toggle_view_mode(request):
    """切换列表/卡片模式"""
    if request.method == 'POST':
        mode = request.POST.get('mode', 'list')
        request.session['view_mode'] = mode
        return HttpResponse(f'Mode set to {mode}')
    return redirect('index')


def ranking_view(request):
    """油滴排行榜"""
    # 获取所有用户，按油滴余额排序，取前50
    top_users = User.objects.filter(
        is_active=True,
        is_banned=False
    ).exclude(
        oil_balance=0
    ).order_by('-oil_balance')[:50]
    
    # 为每个用户补充资源数
    for user in top_users:
        user.resource_count = Resource.objects.filter(
            uploader=user,
            status='published'
        ).count()
    
    # 当前用户的排名
    user_rank = None
    if request.user.is_authenticated:
        # 获取当前用户的油滴排名
        higher_count = User.objects.filter(
            is_active=True,
            is_banned=False,
            oil_balance__gt=request.user.oil_balance
        ).count()
        user_rank = higher_count + 1
    
    context = {
        'top_users': top_users,
        'user_rank': user_rank,
        'total_users': User.objects.filter(is_active=True, is_banned=False).count(),
    }
    
    return render(request, 'ranking.html', context)


# 保留旧的 ranking_view 已替换

def search_view(request):
    """搜索资源"""
    query = request.GET.get('q', '').strip()
    view_mode = request.session.get('view_mode', 'list')
    
    results = []
    search_performed = False
    
    if query:
        search_performed = True
        # 关键词搜索：标题、描述、标签、上传者
        results = Resource.objects.filter(
            Q(status='published') &
            (
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query) |
                Q(uploader__username__icontains=query) |
                Q(uploader__first_name__icontains=query)
            )
        ).select_related('uploader').order_by('-created_at')
    
    # 分页
    paginator = Paginator(results, 10) if results else Paginator([], 10)
    page = request.GET.get('page', 1)
    results_page = paginator.get_page(page)
    
    context = {
        'results': results_page,
        'query': query,
        'search_performed': search_performed,
        'view_mode': view_mode,
        'result_count': results.count(),
    }
    
    return render(request, 'search_results.html', context)