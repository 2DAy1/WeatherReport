from django.db import models


class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "weather_app_city"
        unique_together = ["name", "country"]
        verbose_name_plural = "Cities"

    def __str__(self) -> str:
        return f"{self.name}, {self.country}"


class WeatherData(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="weather_data")
    temperature = models.DecimalField(max_digits=5, decimal_places=2)
    humidity = models.IntegerField()
    pressure = models.IntegerField()
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=10)
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "weather_app_weatherdata"
        verbose_name_plural = "Weather Data"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.city.name} - {self.temperature}°C - {self.created_at}"
