from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Follow


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'oil_balance', 'level', 'is_active', 'is_banned']
    list_filter = ['is_active', 'is_banned', 'level']
    search_fields = ['username', 'email', 'first_name']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('加油哇扩展信息', {
            'fields': ('oil_balance', 'level', 'exp', 'level_title', 'avatar', 'has_used_free_trial', 'daily_free_downloads', 'last_free_date', 'invited_by', 'daily_login_date', 'is_banned'),
        }),
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    search_fields = ['follower__username', 'following__username']
    list_filter = ['created_at']