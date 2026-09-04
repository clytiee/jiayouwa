from django.contrib import admin
from .models import BrowseHistory


@admin.register(BrowseHistory)
class BrowseHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['user__username', 'resource__title']
    ordering = ['-viewed_at']