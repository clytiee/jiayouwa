from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from django.http import HttpResponse
from resources.models import Resource
from users.models import User
from resources.vector_search import VectorSearch


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
    """搜索资源（关键词 + 语义）"""
    query = request.GET.get('q', '').strip()
    
    view_mode = request.GET.get('mode')
    if view_mode in ['list', 'card']:
        request.session['view_mode'] = view_mode
    else:
        view_mode = request.session.get('view_mode', 'list')
    
    results = []
    search_performed = False
    result_count = 0
    
    if query:
        search_performed = True
        
        # 🔍 先用关键词搜索
        keyword_results = Resource.objects.filter(
            Q(status='published') &
            (
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query) |
                Q(uploader__username__icontains=query) |
                Q(uploader__first_name__icontains=query)
            )
        ).select_related('uploader').order_by('-created_at')
        
        # 🧠 再用语义搜索（AI）
        semantic_results = VectorSearch.search(query, limit=20)
        
        # 合并结果：先去重，再按相似度排序
        seen_ids = set()
        combined = []
        
        # 先添加语义搜索的结果（AI 排序）
        for sr in semantic_results:
            if sr['id'] not in seen_ids:
                seen_ids.add(sr['id'])
                combined.append({
                    'resource': None,  # 稍后补充
                    'is_semantic': True,
                    'similarity': sr['similarity'],
                    'data': sr
                })
        
        # 再添加关键词结果
        for kr in keyword_results:
            if kr.id not in seen_ids:
                seen_ids.add(kr.id)
                combined.append({
                    'resource': kr,
                    'is_semantic': False,
                    'similarity': 0,
                    'data': None
                })
        
        # 补充 resource 对象
        resource_ids = [c['data']['id'] for c in combined if c['is_semantic']]
        if resource_ids:
            resource_map = {r.id: r for r in Resource.objects.filter(id__in=resource_ids)}
            for c in combined:
                if c['is_semantic'] and c['data']:
                    c['resource'] = resource_map.get(c['data']['id'])
        
        # 过滤掉没有 resource 的语义结果
        combined = [c for c in combined if c['resource'] is not None]
        
        # 按相似度降序（语义优先），再按创建时间
        combined.sort(key=lambda x: (-x['similarity'] if x['is_semantic'] else 0, -x['resource'].created_at.timestamp()))
        
        # 提取最终的资源列表
        final_resources = [c['resource'] for c in combined]
        result_count = len(final_resources)
        
        # 分页
        paginator = Paginator(final_resources, 10) if final_resources else Paginator([], 10)
        page = request.GET.get('page', 1)
        results_page = paginator.get_page(page)
        
        # 保存语义搜索标记（用于模板显示）
        semantic_ids = {c['resource'].id for c in combined if c['is_semantic']}
        for r in results_page:
            r.is_semantic_match = r.id in semantic_ids
    else:
        results_page = []
    
    context = {
        'results': results_page,
        'query': query,
        'search_performed': search_performed,
        'view_mode': view_mode,
        'result_count': result_count,
    }
    
    return render(request, 'search_results.html', context)