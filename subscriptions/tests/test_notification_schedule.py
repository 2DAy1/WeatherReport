from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from weather.models import City, WeatherData
from subscriptions.models import Subscription
from subscriptions.scheduling import schedule_due_notifications
from subscriptions.tasks.notifications import dispatch_city_notifications


class NotificationScheduleTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="subscriber")
        self.city = City.objects.create(
            name="Kyiv", country="Ukraine", latitude="50.450100", longitude="30.523400",
        )
        self.now = timezone.now()

    def create_subscription(self, period: int = 1) -> Subscription:
        return Subscription.objects.create(
            user=self.user, city=self.city, notification_period=period,
            next_run_at=self.now - timedelta(minutes=1),
        )

    def test_periods_and_city_grouping(self) -> None:
        subscriptions = [self.create_subscription(period) for period in (1, 3, 6, 12)]
        publish = Mock()

        with patch("subscriptions.scheduling.timezone.now", return_value=self.now):
            self.assertEqual(schedule_due_notifications(publish), 4)

        publish.assert_called_once_with(self.city.pk, [sub.pk for sub in subscriptions])
        for sub in subscriptions:
            sub.refresh_from_db()
            self.assertEqual(sub.next_run_at, self.now + timedelta(hours=sub.notification_period))

    def test_inactive_and_future_subscriptions_are_skipped(self) -> None:
        inactive = self.create_subscription()
        inactive.is_active = False
        inactive.save()
        future = self.create_subscription(3)
        future.next_run_at = self.now + timedelta(hours=1)
        future.save()
        publish = Mock()

        self.assertEqual(schedule_due_notifications(publish), 0)
        publish.assert_not_called()

    def test_repeated_scheduler_run_does_not_publish_twice(self) -> None:
        self.create_subscription()
        publish = Mock()

        self.assertEqual(schedule_due_notifications(publish), 1)
        self.assertEqual(schedule_due_notifications(publish), 0)
        publish.assert_called_once()

    def test_publish_failure_does_not_advance_schedule(self) -> None:
        sub = self.create_subscription()
        previous = sub.next_run_at
        publish = Mock(side_effect=ConnectionError("Broker unavailable"))

        with self.assertRaises(ConnectionError):
            schedule_due_notifications(publish)

        sub.refresh_from_db()
        self.assertEqual(sub.next_run_at, previous)

    def test_next_period_only_schedules_subscriptions_that_are_due(self) -> None:
        hourly = self.create_subscription(1)
        self.create_subscription(3)
        publish = Mock()
        with patch("subscriptions.scheduling.timezone.now", return_value=self.now):
            schedule_due_notifications(publish)
        publish.reset_mock()

        with patch("subscriptions.scheduling.timezone.now", return_value=self.now + timedelta(hours=1)):
            self.assertEqual(schedule_due_notifications(publish), 1)

        publish.assert_called_once_with(self.city.pk, [hourly.pk])


class NotificationDispatchTests(TestCase):
    def setUp(self) -> None:
        user = get_user_model().objects.create_user(username="subscriber")
        city = City.objects.create(name="Kyiv", country="Ukraine", latitude=50, longitude=30)
        self.subscription = Subscription.objects.create(
            user=user, city=city, notification_period=1,
            notification_type="both", webhook_url="https://example.com/weather",
        )
        self.weather = WeatherData.objects.create(
            city=city, temperature=18, humidity=60, pressure=1013,
            description="clear sky", icon="01d", wind_speed=3,
        )

    @patch("subscriptions.tasks.webhook.send_webhook_notification.delay")
    @patch("subscriptions.tasks.email.send_email_notification.delay")
    def test_channels_are_dispatched_independently(self, email: Mock, webhook: Mock) -> None:
        for channel, expected_email, expected_webhook in (
            ("email", 1, 0), ("webhook", 0, 1), ("both", 1, 1),
        ):
            with self.subTest(channel=channel):
                self.subscription.notification_type = channel
                self.subscription.save()
                count = dispatch_city_notifications.run(self.weather.pk, [self.subscription.pk])
                self.assertEqual(count, expected_email + expected_webhook)
                self.assertEqual(email.call_count, expected_email)
                self.assertEqual(webhook.call_count, expected_webhook)
                if expected_email:
                    email.assert_called_once_with(self.subscription.pk, self.weather.pk)
                if expected_webhook:
                    webhook.assert_called_once_with(self.subscription.pk, self.weather.pk)
                email.reset_mock()
                webhook.reset_mock()

    @patch("subscriptions.tasks.webhook.send_webhook_notification.delay")
    @patch("subscriptions.tasks.email.send_email_notification.delay")
    def test_disabled_subscription_is_skipped(self, email: Mock, webhook: Mock) -> None:
        self.subscription.is_active = False
        self.subscription.save()

        self.assertEqual(dispatch_city_notifications.run(self.weather.pk, [self.subscription.pk]), 0)
        email.assert_not_called()
        webhook.assert_not_called()

    @patch("subscriptions.tasks.webhook.send_webhook_notification.delay")
    @patch("subscriptions.tasks.email.send_email_notification.delay")
    def test_missing_weather_does_not_send(self, email: Mock, webhook: Mock) -> None:
        self.assertEqual(dispatch_city_notifications.run(None, [self.subscription.pk]), 0)
        email.assert_not_called()
        webhook.assert_not_called()
