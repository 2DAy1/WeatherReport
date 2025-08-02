import requests
import logging
from celery import shared_task, group
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
import concurrent.futures
import time
from .models import City, Subscription, WeatherData, NotificationLog
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


@shared_task
def fetch_weather_data_for_city(city_id):
    """Fetch weather data for a specific city"""
    try:
        city = City.objects.get(id=city_id)
        
        # Check if we have recent weather data (within last 30 minutes)
        recent_data = WeatherData.objects.filter(
            city=city,
            created_at__gte=timezone.now() - timedelta(minutes=30)
        ).first()
        
        if recent_data:
            logger.info(f"Using cached weather data for {city.name}")
            return recent_data.id
        
        # Fetch from OpenWeatherMap API
        api_key = settings.OPENWEATHER_API_KEY
        if not api_key:
            logger.error("OpenWeatherMap API key not configured")
            return None
            
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': city.latitude,
            'lon': city.longitude,
            'appid': api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Create weather data record
        weather_data = WeatherData.objects.create(
            city=city,
            temperature=data['main']['temp'],
            humidity=data['main']['humidity'],
            pressure=data['main']['pressure'],
            description=data['weather'][0]['description'],
            icon=data['weather'][0]['icon'],
            wind_speed=data['wind']['speed']
        )
        
        logger.info(f"Fetched weather data for {city.name}: {weather_data.temperature}°C")
        return weather_data.id
        
    except Exception as e:
        logger.error(f"Error fetching weather data for city {city_id}: {str(e)}")
        return None


@shared_task
def fetch_weather_data_for_cities(city_ids):
    """Fetch weather data for multiple cities in parallel"""
    # Use group to run tasks in parallel
    job = group(fetch_weather_data_for_city.s(city_id) for city_id in city_ids)
    result = job.apply_async()
    return result.get()


@shared_task
def send_email_notification(subscription_id, weather_data_id):
    """Send email notification to a user"""
    try:
        subscription = Subscription.objects.get(id=subscription_id)
        weather_data = WeatherData.objects.get(id=weather_data_id)
        
        # Create notification log
        notification_log = NotificationLog.objects.create(
            subscription=subscription,
            weather_data=weather_data,
            notification_type='email',
            status='pending'
        )
        
        # Prepare email content
        subject = f"Weather Update for {weather_data.city.name}"
        
        context = {
            'user': subscription.user,
            'city': weather_data.city,
            'weather': weather_data,
            'subscription': subscription
        }
        
        html_message = render_to_string('weather_app/email_template.html', context)
        text_message = render_to_string('weather_app/email_template.txt', context)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[subscription.user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        # Update notification log
        notification_log.status = 'success'
        notification_log.save()
        
        logger.info(f"Email notification sent to {subscription.user.email} for {weather_data.city.name}")
        
    except Exception as e:
        logger.error(f"Error sending email notification: {str(e)}")
        if 'notification_log' in locals():
            notification_log.status = 'failed'
            notification_log.error_message = str(e)
            notification_log.save()


@shared_task
def send_webhook_notification(subscription_id, weather_data_id):
    """Send webhook notification"""
    try:
        subscription = Subscription.objects.get(id=subscription_id)
        weather_data = WeatherData.objects.get(id=weather_data_id)
        
        # Create notification log
        notification_log = NotificationLog.objects.create(
            subscription=subscription,
            weather_data=weather_data,
            notification_type='webhook',
            status='pending'
        )
        
        # Prepare webhook payload
        payload = {
            'user_id': subscription.user.id,
            'username': subscription.user.username,
            'city': {
                'name': weather_data.city.name,
                'country': weather_data.city.country
            },
            'weather': {
                'temperature': float(weather_data.temperature),
                'humidity': weather_data.humidity,
                'pressure': weather_data.pressure,
                'description': weather_data.description,
                'wind_speed': float(weather_data.wind_speed)
            },
            'subscription': {
                'notification_period': subscription.notification_period,
                'notification_type': subscription.notification_type
            },
            'timestamp': timezone.now().isoformat()
        }
        
        # Send webhook
        response = requests.post(
            subscription.webhook_url,
            json=payload,
            timeout=settings.WEBHOOK_TIMEOUT,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        
        # Update notification log
        notification_log.status = 'success'
        notification_log.save()
        
        logger.info(f"Webhook notification sent to {subscription.webhook_url} for {weather_data.city.name}")
        
    except Exception as e:
        logger.error(f"Error sending webhook notification: {str(e)}")
        if 'notification_log' in locals():
            notification_log.status = 'failed'
            notification_log.error_message = str(e)
            notification_log.save()


@shared_task
def send_notifications_for_user(user_id):
    """Send notifications for all active subscriptions of a user"""
    try:
        subscriptions = Subscription.objects.filter(
            user_id=user_id,
            is_active=True
        ).select_related('city', 'user')
        
        if not subscriptions:
            return
        
        # Group subscriptions by city to optimize weather API calls
        city_subscriptions = {}
        for subscription in subscriptions:
            city_id = subscription.city.id
            if city_id not in city_subscriptions:
                city_subscriptions[city_id] = []
            city_subscriptions[city_id].append(subscription)
        
        # Fetch weather data for all cities in parallel
        city_ids = list(city_subscriptions.keys())
        weather_data_ids = fetch_weather_data_for_cities(city_ids)
        
        # Send notifications for each subscription
        for city_id, city_subs in city_subscriptions.items():
            weather_data_id = weather_data_ids[city_ids.index(city_id)]
            if weather_data_id:
                for subscription in city_subs:
                    if subscription.notification_type in ['email', 'both']:
                        send_email_notification.delay(subscription.id, weather_data_id)
                    if subscription.notification_type in ['webhook', 'both']:
                        send_webhook_notification.delay(subscription.id, weather_data_id)
        
        logger.info(f"Notifications sent for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error sending notifications for user {user_id}: {str(e)}")


@shared_task
def send_bulk_notifications():
    """Send notifications for all users with active subscriptions"""
    try:
        # Get all users with active subscriptions
        users_with_subscriptions = get_user_model().objects.filter(
            subscriptions__is_active=True
        ).distinct()
        
        # Group subscriptions by notification period
        subscriptions_by_period = {}
        for user in users_with_subscriptions:
            for subscription in user.subscriptions.filter(is_active=True):
                period = subscription.notification_period
                if period not in subscriptions_by_period:
                    subscriptions_by_period[period] = []
                subscriptions_by_period[period].append(subscription)
        
        # Send notifications for each period
        for period, subscriptions in subscriptions_by_period.items():
            # Group by user to send consolidated emails
            user_subscriptions = {}
            for subscription in subscriptions:
                user_id = subscription.user.id
                if user_id not in user_subscriptions:
                    user_subscriptions[user_id] = []
                user_subscriptions[user_id].append(subscription)
            
            # Send notifications for each user
            for user_id in user_subscriptions:
                send_notifications_for_user.delay(user_id)
        
        logger.info("Bulk notifications sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending bulk notifications: {str(e)}")


@shared_task
def cleanup_old_weather_data():
    """Clean up old weather data (older than 7 days)"""
    try:
        cutoff_date = timezone.now() - timedelta(days=7)
        deleted_count = WeatherData.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old weather data records")
        
    except Exception as e:
        logger.error(f"Error cleaning up old weather data: {str(e)}") 