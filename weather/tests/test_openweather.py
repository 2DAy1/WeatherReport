from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from requests import HTTPError, Timeout

from weather.models import City
from weather.openweather import fetch_current_weather


@override_settings(OPENWEATHER_API_KEY="test-api-key")
class OpenWeatherTests(SimpleTestCase):
    def setUp(self) -> None:
        self.city = City(
            name="Kyiv",
            country="Ukraine",
            latitude=Decimal("50.450100"),
            longitude=Decimal("30.523400"),
        )

    @patch("weather.openweather.requests.get")
    def test_fetch_current_returns_weather(self, mock_get: Mock) -> None:
        payload = {
            "main": {"temp": 18.5, "humidity": 60, "pressure": 1013},
            "weather": [{"description": "clear sky", "icon": "01d"}],
            "wind": {"speed": 3.2},
        }
        mock_get.return_value.json.return_value = payload

        result = fetch_current_weather(self.city)

        self.assertEqual(result, payload)
        mock_get.assert_called_once_with(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": self.city.latitude,
                "lon": self.city.longitude,
                "appid": "test-api-key",
                "units": "metric",
            },
            timeout=10,
        )

    @override_settings(OPENWEATHER_API_KEY="")
    @patch("weather.openweather.requests.get")
    def test_missing_api_key_prevents_request(self, mock_get: Mock) -> None:
        with self.assertRaisesMessage(ValueError, "OpenWeatherMap API key is not configured"):
            fetch_current_weather(self.city)

        mock_get.assert_not_called()

    @patch("weather.openweather.requests.get")
    def test_http_error_is_propagated(self, mock_get: Mock) -> None:
        mock_get.return_value.raise_for_status.side_effect = HTTPError("401 Unauthorized")

        with self.assertRaises(HTTPError):
            fetch_current_weather(self.city)

        mock_get.return_value.json.assert_not_called()

    @patch("weather.openweather.requests.get")
    def test_timeout_is_propagated(self, mock_get: Mock) -> None:
        mock_get.side_effect = Timeout("Weather API timed out")

        with self.assertRaises(Timeout):
            fetch_current_weather(self.city)

        mock_get.assert_called_once()
