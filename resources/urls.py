from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    # 发布
    path('upload/', views.resource_upload, name='upload'),
    path('<int:resource_id>/edit/', views.resource_edit, name='edit'),      # ← 编辑
    path('<int:resource_id>/delete/', views.resource_delete, name='delete'), # ← 删除
    
    # 详情
    path('<int:resource_id>/', views.resource_detail, name='detail'),
    
    # 下载
    path('<int:resource_id>/download/', views.resource_download, name='download'),
    path('<int:resource_id>/free-download/', views.free_download, name='free_download'),
    
    # 互动
    path('<int:resource_id>/collect/', views.toggle_collect, name='toggle_collect'),
    path('<int:resource_id>/rate/', views.rate_resource, name='rate_resource'),
    path('<int:resource_id>/comment/', views.add_comment, name='add_comment'),
    path('<int:resource_id>/report-invalid/', views.report_invalid, name='report_invalid'),
    path('comment/<int:comment_id>/vote/', views.vote_comment, name='vote_comment'),
    
    # 用户关注
    path('user/<int:user_id>/follow/', views.toggle_follow, name='toggle_follow'),
    
    # 图片上传API
    path('api/upload-image/', views.upload_preview_image, name='upload_image'),
]