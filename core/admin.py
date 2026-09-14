from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from users.models import User
from resources.models import Resource, Download, Collect, Comment
from shares.models import Share


def dashboard_view(request):
    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)
    
    context = {
        **admin.site.each_context(request),
        'title': '数据概览',
        'total_users': User.objects.count(),
        'active_users_7d': User.objects.filter(last_login__gte=week_ago).count(),
        'new_users_today': User.objects.filter(date_joined__date=today).count(),
        'total_resources': Resource.objects.count(),
        'published_resources': Resource.objects.filter(status='published').count(),
        'new_resources_today': Resource.objects.filter(created_at__date=today).count(),
        'total_downloads': Download.objects.count(),
        'downloads_today': Download.objects.filter(downloaded_at__date=today).count(),
        'total_collects': Collect.objects.filter(is_active=True).count(),
        'total_comments': Comment.objects.filter(audit_status='visible').count(),
        'total_shares': Share.objects.count(),
        'top_resources': Resource.objects.order_by('-download_count')[:10],
        'top_users': User.objects.order_by('-oil_balance')[:10],
    }
    return render(request, 'admin/dashboard.html', context)