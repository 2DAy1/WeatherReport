import logging

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from subscriptions.models import NotificationLog, Subscription
from weather.models import WeatherData

logger = logging.getLogger(__name__)


@shared_task
def send_webhook_notification(subscription_id: int, weather_data_id: int) -> None:
    notification_log = None
    try:
        subscription = Subscription.objects.select_related("user", "city").get(pk=subscription_id)
        weather = WeatherData.objects.select_related("city").get(pk=weather_data_id)
        notification_log = NotificationLog.objects.create(
            subscription=subscription,
            weather_data=weather,
            notification_type="webhook",
            status="pending",
        )
        payload = {
            "user_id": subscription.user_id,
            "username": subscription.user.username,
            "city": {"name": weather.city.name, "country": weather.city.country},
            "weather": {
                "temperature": float(weather.temperature),
                "humidity": weather.humidity,
                "pressure": weather.pressure,
                "description": weather.description,
                "wind_speed": float(weather.wind_speed),
            },
            "subscription": {
                "notification_period": subscription.notification_period,
                "notification_type": subscription.notification_type,
            },
            "timestamp": timezone.now().isoformat(),
        }
        response = requests.post(
            subscription.webhook_url,
            json=payload,
            timeout=settings.WEBHOOK_TIMEOUT,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        notification_log.status = "success"
        notification_log.save(update_fields=["status"])
        logger.info("Webhook notification sent for %s", weather.city.name)
    except Exception as error:
        logger.error("Error sending webhook notification: %s", error)
        if notification_log:
            notification_log.status = "failed"
            notification_log.error_message = str(error)
            notification_log.save(update_fields=["status", "error_message"])
