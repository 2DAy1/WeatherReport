from django.contrib import admin

from .models import NotificationLog, Subscription


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'notification_period', 'notification_type', 'is_active', 'created_at']
    list_filter = ['notification_period', 'notification_type', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'city__name']
    ordering = ['-created_at']


class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'notification_type', 'status', 'sent_at']
    list_filter = ['notification_type', 'status', 'sent_at']
    search_fields = ['subscription__user__username', 'subscription__city__name']
    ordering = ['-sent_at']
    readonly_fields = ['sent_at']
