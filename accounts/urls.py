from rest_framework.routers import SimpleRouter

from .views import RegisterViewSet

router = SimpleRouter()
router.register(r'register', RegisterViewSet, basename='register')
urlpatterns = router.urls
