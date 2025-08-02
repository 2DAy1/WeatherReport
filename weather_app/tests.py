from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from .models import City, Subscription, WeatherData, NotificationLog


class CityModelTest(TestCase):
    def setUp(self):
        self.city = City.objects.create(
            name='Test City',
            country='Test Country',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060')
        )

    def test_city_creation(self):
        self.assertEqual(self.city.name, 'Test City')
        self.assertEqual(self.city.country, 'Test Country')
        self.assertEqual(self.city.latitude, Decimal('40.7128'))
        self.assertEqual(self.city.longitude, Decimal('-74.0060'))

    def test_city_str_representation(self):
        self.assertEqual(str(self.city), 'Test City, Test Country')


class SubscriptionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.city = City.objects.create(
            name='Test City',
            country='Test Country',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060')
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            city=self.city,
            notification_period=1,
            notification_type='email'
        )

    def test_subscription_creation(self):
        self.assertEqual(self.subscription.user, self.user)
        self.assertEqual(self.subscription.city, self.city)
        self.assertEqual(self.subscription.notification_period, 1)
        self.assertEqual(self.subscription.notification_type, 'email')
        self.assertTrue(self.subscription.is_active)

    def test_subscription_str_representation(self):
        expected = f"{self.user.username} - {self.city.name} (1 hour)"
        self.assertEqual(str(self.subscription), expected)


class WeatherDataModelTest(TestCase):
    def setUp(self):
        self.city = City.objects.create(
            name='Test City',
            country='Test Country',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060')
        )
        self.weather_data = WeatherData.objects.create(
            city=self.city,
            temperature=Decimal('25.5'),
            humidity=60,
            pressure=1013,
            description='sunny',
            icon='01d',
            wind_speed=Decimal('5.2')
        )

    def test_weather_data_creation(self):
        self.assertEqual(self.weather_data.city, self.city)
        self.assertEqual(self.weather_data.temperature, Decimal('25.5'))
        self.assertEqual(self.weather_data.humidity, 60)
        self.assertEqual(self.weather_data.pressure, 1013)
        self.assertEqual(self.weather_data.description, 'sunny')
        self.assertEqual(self.weather_data.icon, '01d')
        self.assertEqual(self.weather_data.wind_speed, Decimal('5.2'))

    def test_weather_data_str_representation(self):
        expected = f"{self.city.name} - 25.5°C - {self.weather_data.created_at}"
        self.assertEqual(str(self.weather_data), expected)


class NotificationLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.city = City.objects.create(
            name='Test City',
            country='Test Country',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060')
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            city=self.city,
            notification_period=1,
            notification_type='email'
        )
        self.weather_data = WeatherData.objects.create(
            city=self.city,
            temperature=Decimal('25.5'),
            humidity=60,
            pressure=1013,
            description='sunny',
            icon='01d',
            wind_speed=Decimal('5.2')
        )
        self.notification_log = NotificationLog.objects.create(
            subscription=self.subscription,
            weather_data=self.weather_data,
            notification_type='email',
            status='success'
        )

    def test_notification_log_creation(self):
        self.assertEqual(self.notification_log.subscription, self.subscription)
        self.assertEqual(self.notification_log.weather_data, self.weather_data)
        self.assertEqual(self.notification_log.notification_type, 'email')
        self.assertEqual(self.notification_log.status, 'success')

    def test_notification_log_str_representation(self):
        expected = f"{self.user.username} - {self.city.name} - success"
        self.assertEqual(str(self.notification_log), expected)


class APITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.city = City.objects.create(
            name='Test City',
            country='Test Country',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060')
        )

    def test_register_user(self):
        url = reverse('register-list')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)

    def test_get_cities_authenticated(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('city-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_cities_unauthenticated(self):
        url = reverse('city-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_cities(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('city-search')
        response = self.client.get(url, {'q': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_subscription(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('subscription-list')
        data = {
            'city': self.city.id,
            'notification_period': 1,
            'notification_type': 'email'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Subscription.objects.count(), 1)

    def test_get_user_subscriptions(self):
        subscription = Subscription.objects.create(
            user=self.user,
            city=self.city,
            notification_period=1,
            notification_type='email'
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('subscription-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1) 