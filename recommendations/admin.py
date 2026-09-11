from django.contrib import admin
from .models import BrowseHistory, Behavior


@admin.register(BrowseHistory)
class BrowseHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['user__username', 'resource__title']
    ordering = ['-viewed_at']


@admin.register(Behavior)
class BehaviorAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'action', 'resource', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username', 'resource__title']
    ordering = ['-created_at']
    readonly_fields = ['user', 'resource', 'action', 'extra_data', 'session_id', 'device_id', 'ip_address', 'created_at']