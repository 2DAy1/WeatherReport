from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterViewSet, CityViewSet, SubscriptionViewSet, 
    WeatherDataViewSet, NotificationLogViewSet
)

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='register')
router.register(r'cities', CityViewSet, basename='city')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'weather', WeatherDataViewSet, basename='weather')
router.register(r'notifications', NotificationLogViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
] 