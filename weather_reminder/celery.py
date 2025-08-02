import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_reminder.settings')

app = Celery('weather_reminder')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'send-weather-notifications-every-hour': {
        'task': 'weather_app.tasks.send_bulk_notifications',
        'schedule': crontab(minute=0, hour='*'),  # Every hour at minute 0
    },
    'cleanup-old-weather-data-daily': {
        'task': 'weather_app.tasks.cleanup_old_weather_data',
        'schedule': crontab(minute=0, hour=2),  # Daily at 2 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 