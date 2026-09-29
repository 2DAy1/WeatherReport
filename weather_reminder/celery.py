import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_reminder.settings')

app = Celery('weather_reminder')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-due-weather-notifications': {
        'task': 'subscriptions.tasks.notifications.send_bulk_notifications',
        'schedule': crontab(minute='*'),
    },
    'cleanup-old-weather-data-daily': {
        'task': 'weather.tasks.cleanup_old_weather_data',
        'schedule': crontab(minute=0, hour=2),
    },
}
