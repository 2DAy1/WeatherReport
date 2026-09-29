from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from subscriptions.models import Subscription
from weather.models import City


CITIES = (
    ("New York", "USA", "40.7128", "-74.0060"),
    ("London", "UK", "51.5074", "-0.1278"),
    ("Tokyo", "Japan", "35.6762", "139.6503"),
    ("Paris", "France", "48.8566", "2.3522"),
    ("Sydney", "Australia", "-33.8688", "151.2093"),
    ("Berlin", "Germany", "52.5200", "13.4050"),
    ("Moscow", "Russia", "55.7558", "37.6176"),
    ("Toronto", "Canada", "43.6532", "-79.3832"),
    ("São Paulo", "Brazil", "-23.5505", "-46.6333"),
    ("Cairo", "Egypt", "30.0444", "31.2357"),
)
USERS = (
    ("john_doe", "john@example.com", "John", "Doe"),
    ("jane_smith", "jane@example.com", "Jane", "Smith"),
    ("bob_wilson", "bob@example.com", "Bob", "Wilson"),
)
SUBSCRIPTIONS = (
    ("john_doe", "New York", 1, "email"),
    ("john_doe", "London", 3, "webhook"),
    ("jane_smith", "Tokyo", 3, "both"),
    ("bob_wilson", "Paris", 1, "email"),
    ("bob_wilson", "Sydney", 6, "webhook"),
)


class Command(BaseCommand):
    help = "Populate the database with sample cities, users and subscriptions"

    def handle(self, *args: object, **options: object) -> None:
        created_cities = 0
        for name, country, latitude, longitude in CITIES:
            _, created = City.objects.get_or_create(
                name=name, country=country,
                defaults={"latitude": Decimal(latitude), "longitude": Decimal(longitude)},
            )
            created_cities += created

        created_users = 0
        for username, email, first_name, last_name in USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email, "first_name": first_name, "last_name": last_name},
            )
            if created:
                user.set_password("password123")
                user.save(update_fields=["password"])
                created_users += 1

        created_subscriptions = 0
        for username, city_name, period, channel in SUBSCRIPTIONS:
            _, created = Subscription.objects.get_or_create(
                user=User.objects.get(username=username),
                city=City.objects.get(name=city_name),
                notification_period=period,
                defaults={
                    "notification_type": channel,
                    "webhook_url": "https://example.com/weather" if channel != "email" else "",
                    "is_active": channel == "email",
                },
            )
            created_subscriptions += created

        self.stdout.write(self.style.SUCCESS(
            f"Created {created_cities} cities, {created_users} users, "
            f"{created_subscriptions} subscriptions."
        ))
