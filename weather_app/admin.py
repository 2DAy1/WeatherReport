from django.contrib import admin
from .models import City, Subscription, WeatherData, NotificationLog


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'latitude', 'longitude', 'created_at']
    list_filter = ['country', 'created_at']
    search_fields = ['name', 'country']
    ordering = ['name']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'notification_period', 'notification_type', 'is_active', 'created_at']
    list_filter = ['notification_period', 'notification_type', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'city__name']
    ordering = ['-created_at']


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['city', 'temperature', 'humidity', 'pressure', 'description', 'created_at']
    list_filter = ['created_at', 'city']
    search_fields = ['city__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'notification_type', 'status', 'sent_at']
    list_filter = ['notification_type', 'status', 'sent_at']
    search_fields = ['subscription__user__username', 'subscription__city__name']
    ordering = ['-sent_at']
    readonly_fields = ['sent_at'] 