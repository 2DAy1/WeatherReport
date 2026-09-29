from django.contrib import admin

from .models import City, WeatherData


class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'latitude', 'longitude', 'created_at']
    list_filter = ['country', 'created_at']
    search_fields = ['name', 'country']
    ordering = ['name']


class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['city', 'temperature', 'humidity', 'pressure', 'description', 'created_at']
    list_filter = ['created_at', 'city']
    search_fields = ['city__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
