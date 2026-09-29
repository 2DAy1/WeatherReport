from contextlib import redirect_stdout
from email import policy
from email.parser import Parser
from io import StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from weather.models import City, WeatherData
from subscriptions.models import NotificationLog, Subscription
from subscriptions.tasks.email import send_email_notification


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
    DEFAULT_FROM_EMAIL="weather@localhost",
)
class EmailNotificationTests(TestCase):
    def test_notification_is_printed_and_logged(self) -> None:
        user = get_user_model().objects.create_user(
            username="subscriber", email="subscriber@example.com",
        )
        city = City.objects.create(
            name="Kyiv", country="Ukraine", latitude="50.450100", longitude="30.523400",
        )
        subscription = Subscription.objects.create(
            user=user, city=city, notification_period=1, notification_type="email",
        )
        weather = WeatherData.objects.create(
            city=city, temperature="18.50", humidity=60, pressure=1013,
            description="clear sky", icon="01d", wind_speed="3.20",
        )
        output = StringIO()

        with redirect_stdout(output):
            send_email_notification.run(subscription.pk, weather.pk)

        message = Parser(policy=policy.default).parsestr(output.getvalue())
        self.assertEqual(message["Subject"], "Weather Update for Kyiv")
        self.assertEqual(message["From"], "weather@localhost")
        self.assertEqual(message["To"], user.email)
        self.assertIn("18.50", message.get_body(preferencelist=("plain",)).get_content())
        self.assertIn("Kyiv", message.get_body(preferencelist=("html",)).get_content())
        log = NotificationLog.objects.get(subscription=subscription)
        self.assertEqual(log.weather_data_id, weather.pk)
        self.assertEqual(log.notification_type, "email")
        self.assertEqual(log.status, "success")
