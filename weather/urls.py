from rest_framework.routers import SimpleRouter

from .views import CityViewSet, WeatherDataViewSet

router = SimpleRouter()
router.register(r'cities', CityViewSet, basename='city')
router.register(r'weather', WeatherDataViewSet, basename='weather')
urlpatterns = router.urls
