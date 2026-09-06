from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import home_view, ranking_view, toggle_view_mode, search_view

urlpatterns = [
    path('', home_view, name='index'),
    path('ranking/', ranking_view, name='ranking'),
    path('toggle-mode/', toggle_view_mode, name='toggle_mode'),
    path('search/', search_view, name='search'),  # ← 添加搜索
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('resource/', include('resources.urls')),
    path('s/', include('shares.urls')),
    path('notifications/', include('notifications.urls')),
    path('contact/', include('contact.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)