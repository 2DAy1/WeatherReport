from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class City(models.Model):
    """Model for storing city information"""
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'country']
        verbose_name_plural = 'Cities'

    def __str__(self):
        return f"{self.name}, {self.country}"


class Subscription(models.Model):
    """Model for storing user subscriptions to weather notifications"""
    NOTIFICATION_PERIODS = [
        (1, '1 hour'),
        (2, '2 hours'),
        (3, '3 hours'),
    ]
    
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('webhook', 'Webhook'),
        ('both', 'Both'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='subscriptions')
    notification_period = models.IntegerField(
        choices=NOTIFICATION_PERIODS,
        validators=[MinValueValidator(1), MaxValueValidator(3)]
    )
    notification_type = models.CharField(
        max_length=10,
        choices=NOTIFICATION_TYPES,
        default='email'
    )
    webhook_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'city', 'notification_period']
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"{self.user.username} - {self.city.name} ({self.get_notification_period_display()})"


class WeatherData(models.Model):
    """Model for storing weather data to avoid duplicate API calls"""
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='weather_data')
    temperature = models.DecimalField(max_digits=5, decimal_places=2)
    humidity = models.IntegerField()
    pressure = models.IntegerField()
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=10)
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Weather Data'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.city.name} - {self.temperature}°C - {self.created_at}"


class NotificationLog(models.Model):
    """Model for storing notification logs"""
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='notifications')
    weather_data = models.ForeignKey(WeatherData, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=10)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Notification Logs'
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.subscription.user.username} - {self.subscription.city.name} - {self.status}" 