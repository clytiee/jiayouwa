from django.urls import path
from . import views

app_name = 'shares'

urlpatterns = [
    path('create/', views.create_share, name='create_share'),
    path('<str:share_id>/', views.share_landing, name='landing'),
]