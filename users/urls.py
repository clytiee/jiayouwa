from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # 注册
    path('register/', views.register_view, name='register'),
    path('activate/<str:uidb64>/<str:token>/', views.activate_view, name='activate'),
    
    # 登录/登出
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # 用户中心
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    
    # 我的资源
    path('my-resources/', views.my_resources_view, name='my_resources'),
    path('my-collections/', views.my_collections_view, name='my_collections'),
    path('my-downloads/', views.my_downloads_view, name='my_downloads'),
    path('my-follows/', views.my_follows_view, name='my_follows'),
    path('my-history/', views.my_history_view, name='my_history'),
    path('my-history/clear/', views.clear_history_view, name='clear_history'),
    
    # 分享历史和收益
    path('my-shares/', views.my_shares_view, name='my_shares'),
    path('my-earnings/', views.my_earnings_view, name='my_earnings'),
]