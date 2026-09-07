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
    """综合排行榜（支持多维度）"""
    
    rank_type = request.GET.get('type', 'download')
    
    # 1. 油滴排行榜（保持不变）
    oil_top_users = User.objects.filter(
        is_active=True,
        is_banned=False
    ).exclude(
        oil_balance=0
    ).order_by('-oil_balance')[:50]
    
    for user in oil_top_users:
        user.resource_count = Resource.objects.filter(
            uploader=user,
            status='published'
        ).count()
    
    user_rank = None
    if request.user.is_authenticated:
        higher_count = User.objects.filter(
            is_active=True,
            is_banned=False,
            oil_balance__gt=request.user.oil_balance
        ).count()
        user_rank = higher_count + 1
    
    # ===== 资源排行榜（根据类型选择） =====
    resources_list = []
    
    if rank_type == 'download':
        resources_list = Resource.objects.filter(
            status='published'
        ).order_by('-download_count')[:30]
    
    elif rank_type == 'free_download':
        resources_list = Resource.objects.filter(
            status='published',
            price=0
        ).order_by('-download_count')[:30]
    
    elif rank_type == 'collect':
        resources_list = Resource.objects.filter(
            status='published'
        ).order_by('-collect_count')[:30]
    
    elif rank_type == 'comment':
        resources_list = Resource.objects.filter(
            status='published'
        ).annotate(
            comment_count=Count('comment')
        ).filter(
            comment_count__gt=0
        ).order_by('-comment_count')[:30]
    
    # 补充上传者名称
    for r in resources_list:
        r.uploader_name = r.uploader.first_name or r.uploader.username
        if rank_type == 'comment':
            r.comment_count = getattr(r, 'comment_count', 0)
    
    context = {
        'rank_type': rank_type,
        'resources_list': resources_list,  # ← 统一变量名
        'oil_top_users': oil_top_users,
        'user_rank': user_rank,
        'total_users': User.objects.filter(is_active=True, is_banned=False).count(),
    }
    
    return render(request, 'ranking.html', context)

def search_view(request):
    """搜索资源（支持精确/模糊匹配）"""
    query = request.GET.get('q', '').strip()
    match_type = request.GET.get('match', 'exact')
    
    view_mode = request.GET.get('mode')
    if view_mode in ['list', 'card']:
        request.session['view_mode'] = view_mode
    else:
        view_mode = request.session.get('view_mode', 'list')
    
    results = []
    search_performed = False
    result_count = 0
    final_resources = []
    
    if query:
        search_performed = True
        
        if match_type == 'exact':
            # 🎯 精确匹配：标题包含所有关键词（无关顺序）
            keywords = query.split()
            q_filter = Q(status='published')
            for kw in keywords:
                q_filter &= Q(title__icontains=kw)
            
            keyword_results = Resource.objects.filter(
                q_filter
            ).select_related('uploader').order_by('-created_at')
            
            final_resources = list(keyword_results)
            result_count = len(final_resources)
            results_page = Paginator(final_resources, 10).get_page(request.GET.get('page', 1))
            
        else:
            # 🔍 模糊匹配：原有逻辑
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
            
            # 语义搜索
            semantic_results = VectorSearch.search(query, limit=20)
            
            seen_ids = set()
            combined = []
            
            for sr in semantic_results:
                resource_id = sr['id']
                if resource_id not in seen_ids:
                    seen_ids.add(resource_id)
                    try:
                        resource = Resource.objects.get(id=resource_id, status='published')
                        combined.append({
                            'resource': resource,
                            'is_semantic': True,
                            'similarity': sr.get('similarity', 0),
                        })
                    except Resource.DoesNotExist:
                        pass
            
            for kr in keyword_results:
                if kr.id not in seen_ids:
                    seen_ids.add(kr.id)
                    combined.append({
                        'resource': kr,
                        'is_semantic': False,
                        'similarity': 0,
                    })
            
            combined.sort(key=lambda x: (-x['similarity'] if x['is_semantic'] else -1, -x['resource'].created_at.timestamp()))
            
            final_resources = [item['resource'] for item in combined]
            result_count = len(final_resources)
            
            for item in combined:
                if item['is_semantic']:
                    item['resource'].is_semantic_match = True
            
            results_page = Paginator(final_resources, 10).get_page(request.GET.get('page', 1))
            
            for r in results_page:
                for item in combined:
                    if item['resource'].id == r.id:
                        r.is_semantic_match = item['is_semantic']
                        break
    
    else:
        results_page = []
    
    context = {
        'results': results_page,
        'query': query,
        'search_performed': search_performed,
        'view_mode': view_mode,
        'result_count': result_count,
        'match_type': match_type,
    }
    
    return render(request, 'search_results.html', context)