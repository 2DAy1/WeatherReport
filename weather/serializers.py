from rest_framework import serializers

from .models import City, WeatherData


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'


class WeatherDataSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = WeatherData
        fields = '__all__'
