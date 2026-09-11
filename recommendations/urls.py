from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('track/', views.track_behavior, name='track'),
]