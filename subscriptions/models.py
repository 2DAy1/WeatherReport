from django.conf import settings
from django.db import models
from django.utils import timezone

from weather.models import City, WeatherData


class Subscription(models.Model):
    NOTIFICATION_PERIODS = [(1, "1 hour"), (3, "3 hours"), (6, "6 hours"), (12, "12 hours")]
    NOTIFICATION_TYPES = [("email", "Email"), ("webhook", "Webhook"), ("both", "Both")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="subscriptions")
    notification_period = models.IntegerField(choices=NOTIFICATION_PERIODS)
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default="email")
    webhook_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    next_run_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "weather_app_subscription"
        unique_together = ["user", "city", "notification_period"]
        verbose_name_plural = "Subscriptions"

    def __str__(self) -> str:
        return f"{self.user.username} - {self.city.name} ({self.get_notification_period_display()})"


class NotificationLog(models.Model):
    STATUS_CHOICES = [("success", "Success"), ("failed", "Failed"), ("pending", "Pending")]

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="notifications")
    weather_data = models.ForeignKey(WeatherData, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=10)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "weather_app_notificationlog"
        verbose_name_plural = "Notification Logs"
        ordering = ["-sent_at"]

    def __str__(self) -> str:
        return f"{self.subscription.user.username} - {self.subscription.city.name} - {self.status}"
