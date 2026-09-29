from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from requests import Timeout

from subscriptions.models import NotificationLog, Subscription
from subscriptions.tasks.webhook import send_webhook_notification
from weather.models import City, WeatherData


@override_settings(WEBHOOK_TIMEOUT=5)
class WebhookNotificationTests(TestCase):
    def setUp(self) -> None:
        user = get_user_model().objects.create_user(username="subscriber")
        city = City.objects.create(
            name="Kyiv", country="Ukraine", latitude="50.450100", longitude="30.523400",
        )
        self.subscription = Subscription.objects.create(
            user=user, city=city, notification_period=1,
            notification_type="webhook", webhook_url="https://example.com/weather",
        )
        self.weather = WeatherData.objects.create(
            city=city, temperature="18.50", humidity=60, pressure=1013,
            description="clear sky", icon="01d", wind_speed="3.20",
        )

    @patch("subscriptions.tasks.webhook.requests.post")
    def test_success_sends_weather_and_logs_delivery(self, post: Mock) -> None:
        send_webhook_notification.run(self.subscription.pk, self.weather.pk)

        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args, (self.subscription.webhook_url,))
        self.assertEqual(kwargs["timeout"], 5)
        self.assertEqual(kwargs["json"]["city"], {"name": "Kyiv", "country": "Ukraine"})
        self.assertEqual(kwargs["json"]["weather"]["temperature"], 18.5)
        post.return_value.raise_for_status.assert_called_once_with()
        self.assertEqual(NotificationLog.objects.get().status, "success")

    @patch("subscriptions.tasks.webhook.requests.post")
    def test_timeout_is_logged_as_failure(self, post: Mock) -> None:
        post.side_effect = Timeout("receiver timed out")

        with self.assertLogs("subscriptions.tasks.webhook", level="ERROR"):
            send_webhook_notification.run(self.subscription.pk, self.weather.pk)

        log = NotificationLog.objects.get()
        self.assertEqual(log.status, "failed")
        self.assertIn("receiver timed out", log.error_message)
