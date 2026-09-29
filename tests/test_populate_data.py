from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from subscriptions.models import Subscription
from weather.models import City


class PopulateDataTests(TestCase):
    def test_command_creates_idempotent_sample_data(self) -> None:
        call_command("populate_data")
        call_command("populate_data")

        self.assertEqual(City.objects.count(), 10)
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(Subscription.objects.count(), 5)
        self.assertTrue(User.objects.get(username="john_doe").check_password("password123"))
        self.assertFalse(Subscription.objects.get(notification_type="both").is_active)
