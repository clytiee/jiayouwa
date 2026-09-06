from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    path('', views.contact_create, name='create'),
    path('history/', views.contact_history, name='history'),
]