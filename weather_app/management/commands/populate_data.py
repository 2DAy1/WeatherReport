from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from weather_app.models import City, Subscription
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate database with sample cities and users'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample cities...')
        
        # Sample cities data
        cities_data = [
            {'name': 'New York', 'country': 'USA', 'latitude': Decimal('40.7128'), 'longitude': Decimal('-74.0060')},
            {'name': 'London', 'country': 'UK', 'latitude': Decimal('51.5074'), 'longitude': Decimal('-0.1278')},
            {'name': 'Tokyo', 'country': 'Japan', 'latitude': Decimal('35.6762'), 'longitude': Decimal('139.6503')},
            {'name': 'Paris', 'country': 'France', 'latitude': Decimal('48.8566'), 'longitude': Decimal('2.3522')},
            {'name': 'Sydney', 'country': 'Australia', 'latitude': Decimal('-33.8688'), 'longitude': Decimal('151.2093')},
            {'name': 'Berlin', 'country': 'Germany', 'latitude': Decimal('52.5200'), 'longitude': Decimal('13.4050')},
            {'name': 'Moscow', 'country': 'Russia', 'latitude': Decimal('55.7558'), 'longitude': Decimal('37.6176')},
            {'name': 'Toronto', 'country': 'Canada', 'latitude': Decimal('43.6532'), 'longitude': Decimal('-79.3832')},
            {'name': 'São Paulo', 'country': 'Brazil', 'latitude': Decimal('-23.5505'), 'longitude': Decimal('-46.6333')},
            {'name': 'Cairo', 'country': 'Egypt', 'latitude': Decimal('30.0444'), 'longitude': Decimal('31.2357')},
        ]
        
        created_cities = []
        for city_data in cities_data:
            city, created = City.objects.get_or_create(
                name=city_data['name'],
                country=city_data['country'],
                defaults={
                    'latitude': city_data['latitude'],
                    'longitude': city_data['longitude']
                }
            )
            if created:
                created_cities.append(city)
                self.stdout.write(f'Created city: {city}')
        
        self.stdout.write(f'Created {len(created_cities)} new cities')
        
        # Create sample users
        self.stdout.write('Creating sample users...')
        
        users_data = [
            {'username': 'john_doe', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'username': 'jane_smith', 'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'username': 'bob_wilson', 'email': 'bob@example.com', 'first_name': 'Bob', 'last_name': 'Wilson'},
        ]
        
        created_users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'password': 'password123'  # In production, use proper password hashing
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                created_users.append(user)
                self.stdout.write(f'Created user: {user.username}')
        
        self.stdout.write(f'Created {len(created_users)} new users')
        
        # Create sample subscriptions
        self.stdout.write('Creating sample subscriptions...')
        
        subscription_data = [
            {'user': 'john_doe', 'city': 'New York', 'notification_period': 1, 'notification_type': 'email'},
            {'user': 'john_doe', 'city': 'London', 'notification_period': 2, 'notification_type': 'webhook', 'webhook_url': 'https://webhook.site/your-unique-url'},
            {'user': 'jane_smith', 'city': 'Tokyo', 'notification_period': 3, 'notification_type': 'both', 'webhook_url': 'https://webhook.site/your-unique-url'},
            {'user': 'bob_wilson', 'city': 'Paris', 'notification_period': 1, 'notification_type': 'email'},
            {'user': 'bob_wilson', 'city': 'Sydney', 'notification_period': 2, 'notification_type': 'webhook', 'webhook_url': 'https://webhook.site/your-unique-url'},
        ]
        
        created_subscriptions = []
        for sub_data in subscription_data:
            user = User.objects.get(username=sub_data['user'])
            city = City.objects.get(name=sub_data['city'])
            
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                city=city,
                notification_period=sub_data['notification_period'],
                defaults={
                    'notification_type': sub_data['notification_type'],
                    'webhook_url': sub_data.get('webhook_url', ''),
                    'is_active': True
                }
            )
            if created:
                created_subscriptions.append(subscription)
                self.stdout.write(f'Created subscription: {user.username} - {city.name}')
        
        self.stdout.write(f'Created {len(created_subscriptions)} new subscriptions')
        self.stdout.write(self.style.SUCCESS('Database population completed successfully!')) 