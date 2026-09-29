import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import City, WeatherData
from .openweather import fetch_current_weather

logger = logging.getLogger(__name__)


@shared_task
def fetch_weather_data_for_city(city_id: int) -> int | None:
    try:
        city = City.objects.get(pk=city_id)
        cached = WeatherData.objects.filter(
            city=city,
            created_at__gte=timezone.now() - timedelta(minutes=30),
        ).first()
        if cached:
            logger.info("Using cached weather data for %s", city.name)
            return cached.pk

        data = fetch_current_weather(city)
        weather = WeatherData.objects.create(
            city=city,
            temperature=data["main"]["temp"],
            humidity=data["main"]["humidity"],
            pressure=data["main"]["pressure"],
            description=data["weather"][0]["description"],
            icon=data["weather"][0]["icon"],
            wind_speed=data["wind"]["speed"],
        )
        logger.info("Fetched weather data for %s: %s°C", city.name, weather.temperature)
        return weather.pk
    except Exception as error:
        logger.error("Error fetching weather data for city %s: %s", city_id, error)
        return None


@shared_task
def cleanup_old_weather_data() -> None:
    try:
        cutoff = timezone.now() - timedelta(days=7)
        deleted_count, _ = WeatherData.objects.filter(created_at__lt=cutoff).delete()
        logger.info("Cleaned up %s old weather data records", deleted_count)
    except Exception as error:
        logger.error("Error cleaning up old weather data: %s", error)
