from rest_framework import serializers

from .models import NotificationLog, Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    city_country = serializers.CharField(source='city.country', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_username', 'city', 'city_name', 'city_country',
            'notification_period', 'notification_type', 'webhook_url', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate(self, data):
        notification_type = data.get('notification_type', getattr(self.instance, 'notification_type', None))
        webhook_url = data.get('webhook_url', getattr(self.instance, 'webhook_url', None))
        if notification_type in ('webhook', 'both') and not webhook_url:
            raise serializers.ValidationError("Webhook URL is required for webhook notifications.")
        return data


class NotificationLogSerializer(serializers.ModelSerializer):
    subscription_info = serializers.CharField(source='subscription', read_only=True)

    class Meta:
        model = NotificationLog
        fields = '__all__'
        read_only_fields = ['id', 'sent_at']
