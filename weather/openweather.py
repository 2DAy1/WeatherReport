from typing import Any

import requests
from django.conf import settings

from .models import City


def fetch_current_weather(city: City) -> dict[str, Any]:
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        raise ValueError("OpenWeatherMap API key is not configured")

    response = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={
            "lat": city.latitude,
            "lon": city.longitude,
            "appid": api_key,
            "units": "metric",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
