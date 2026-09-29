from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone
from requests import Timeout

from weather.models import City, WeatherData
from weather.tasks import fetch_weather_data_for_city


class WeatherTaskTests(TestCase):
    def setUp(self) -> None:
        self.city = City.objects.create(
            name="Kyiv", country="Ukraine",
            latitude="50.450100", longitude="30.523400",
        )
        self.payload = {
            "main": {"temp": 18.5, "humidity": 60, "pressure": 1013},
            "weather": [{"description": "clear sky", "icon": "01d"}],
            "wind": {"speed": 3.2},
        }

    def create_weather(self) -> WeatherData:
        return WeatherData.objects.create(
            city=self.city, temperature="10.00", humidity=70, pressure=1000,
            description="cloudy", icon="03d", wind_speed="2.00",
        )

    @patch("weather.tasks.fetch_current_weather")
    def test_fetch_stores_weather(self, fetch: Mock) -> None:
        fetch.return_value = self.payload

        weather_id = fetch_weather_data_for_city.run(self.city.pk)

        weather = WeatherData.objects.get(pk=weather_id)
        self.assertEqual(weather.city_id, self.city.pk)
        self.assertEqual(weather.temperature, Decimal("18.50"))
        self.assertEqual(weather.humidity, 60)
        self.assertEqual(weather.pressure, 1013)
        self.assertEqual(weather.description, "clear sky")
        self.assertEqual(weather.icon, "01d")
        self.assertEqual(weather.wind_speed, Decimal("3.20"))
        fetch.assert_called_once_with(self.city)

    @patch("weather.tasks.fetch_current_weather")
    def test_fresh_cache_skips_api(self, fetch: Mock) -> None:
        cached = self.create_weather()

        weather_id = fetch_weather_data_for_city.run(self.city.pk)

        self.assertEqual(weather_id, cached.pk)
        self.assertEqual(WeatherData.objects.count(), 1)
        fetch.assert_not_called()

    @patch("weather.tasks.fetch_current_weather")
    def test_expired_cache_fetches_new_weather(self, fetch: Mock) -> None:
        cached = self.create_weather()
        WeatherData.objects.filter(pk=cached.pk).update(
            created_at=timezone.now() - timedelta(minutes=31),
        )
        fetch.return_value = self.payload

        weather_id = fetch_weather_data_for_city.run(self.city.pk)

        self.assertNotEqual(weather_id, cached.pk)
        self.assertEqual(WeatherData.objects.count(), 2)
        self.assertEqual(WeatherData.objects.get(pk=weather_id).temperature, Decimal("18.50"))
        fetch.assert_called_once_with(self.city)

    @patch("weather.tasks.fetch_current_weather")
    def test_api_failure_does_not_create_weather(self, fetch: Mock) -> None:
        fetch.side_effect = Timeout("Weather API timed out")

        with self.assertLogs("weather.tasks", level="ERROR"):
            weather_id = fetch_weather_data_for_city.run(self.city.pk)

        self.assertIsNone(weather_id)
        self.assertFalse(WeatherData.objects.exists())
