from rest_framework.routers import SimpleRouter

from .views import NotificationLogViewSet, SubscriptionViewSet

router = SimpleRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'notifications', NotificationLogViewSet, basename='notification')
urlpatterns = router.urls
