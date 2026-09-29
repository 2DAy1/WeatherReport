from celery import chain, shared_task
from django.db.models import QuerySet

from subscriptions.scheduling import schedule_due_notifications
from subscriptions.tasks.email import send_email_notification
from subscriptions.tasks.webhook import send_webhook_notification
from subscriptions.models import Subscription
from weather.models import WeatherData
from weather.tasks import fetch_weather_data_for_city


def publish_city_notifications(city_id: int, subscription_ids: list[int]) -> None:
    chain(
        fetch_weather_data_for_city.s(city_id),
        dispatch_city_notifications.s(subscription_ids),
    ).apply_async()


@shared_task
def dispatch_city_notifications(
    weather_data_id: int | None,
    subscription_ids: list[int],
) -> int:
    if weather_data_id is None:
        return 0

    weather = WeatherData.objects.get(pk=weather_data_id)
    subscriptions: QuerySet[Subscription] = Subscription.objects.filter(
        pk__in=subscription_ids,
        city_id=weather.city_id,
        is_active=True,
    )
    queued = 0
    for subscription in subscriptions:
        if subscription.notification_type in ("email", "both"):
            send_email_notification.delay(subscription.pk, weather.pk)
            queued += 1
        if subscription.notification_type in ("webhook", "both"):
            send_webhook_notification.delay(subscription.pk, weather.pk)
            queued += 1
    return queued


@shared_task
def send_bulk_notifications() -> int:
    return schedule_due_notifications(publish_city_notifications)
