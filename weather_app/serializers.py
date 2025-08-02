from rest_framework import serializers
from django.contrib.auth.models import User
from .models import City, Subscription, WeatherData, NotificationLog


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'


class WeatherDataSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    
    class Meta:
        model = WeatherData
        fields = '__all__'


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
        # Ensure webhook_url is provided when notification_type is webhook or both
        if data.get('notification_type') in ['webhook', 'both'] and not data.get('webhook_url'):
            raise serializers.ValidationError("Webhook URL is required for webhook notifications.")
        return data


class NotificationLogSerializer(serializers.ModelSerializer):
    subscription_info = serializers.CharField(source='subscription', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = '__all__'
        read_only_fields = ['id', 'sent_at']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user 