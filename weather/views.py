from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import City, WeatherData
from .serializers import CitySerializer, WeatherDataSerializer


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.order_by("name", "pk")
    serializer_class = CitySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if query:
            cities = City.objects.filter(
                Q(name__icontains=query) | Q(country__icontains=query)
            )[:10]
            serializer = self.get_serializer(cities, many=True)
            return Response(serializer.data)
        return Response([])


class WeatherDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WeatherData.objects.all()
    serializer_class = WeatherDataSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_city(self, request):
        city_id = request.query_params.get('city_id')
        if city_id:
            weather_data = WeatherData.objects.filter(city_id=city_id).first()
            if weather_data:
                serializer = self.get_serializer(weather_data)
                return Response(serializer.data)
            return Response({'message': 'No weather data found for this city'},
                          status=status.HTTP_404_NOT_FOUND)
        return Response({'message': 'city_id parameter is required'},
                       status=status.HTTP_400_BAD_REQUEST)
