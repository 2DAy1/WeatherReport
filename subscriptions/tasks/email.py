import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from subscriptions.models import NotificationLog, Subscription
from weather.models import WeatherData

logger = logging.getLogger(__name__)


@shared_task
def send_email_notification(subscription_id: int, weather_data_id: int) -> None:
    notification_log = None
    try:
        subscription = Subscription.objects.select_related("user", "city").get(pk=subscription_id)
        weather = WeatherData.objects.select_related("city").get(pk=weather_data_id)
        notification_log = NotificationLog.objects.create(
            subscription=subscription,
            weather_data=weather,
            notification_type="email",
            status="pending",
        )

        context = {
            "user": subscription.user,
            "city": weather.city,
            "weather": weather,
            "subscription": subscription,
        }
        send_mail(
            subject=f"Weather Update for {weather.city.name}",
            message=render_to_string("subscriptions/email_template.txt", context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[subscription.user.email],
            html_message=render_to_string("subscriptions/email_template.html", context),
            fail_silently=False,
        )
        notification_log.status = "success"
        notification_log.save(update_fields=["status"])
        logger.info("Email notification sent to %s for %s", subscription.user.email, weather.city.name)
    except Exception as error:
        logger.error("Error sending email notification: %s", error)
        if notification_log:
            notification_log.status = "failed"
            notification_log.error_message = str(error)
            notification_log.save(update_fields=["status", "error_message"])
