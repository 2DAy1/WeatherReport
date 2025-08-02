from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.db.models import Q
from .models import City, Subscription, WeatherData, NotificationLog
from .serializers import (
    UserSerializer, CitySerializer, SubscriptionSerializer, 
    WeatherDataSerializer, NotificationLogSerializer, RegisterSerializer
)


class RegisterViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User registered successfully',
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.all()
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


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        subscription = self.get_object()
        subscription.is_active = not subscription.is_active
        subscription.save()
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        subscriptions = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)


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


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationLog.objects.filter(subscription__user=self.request.user)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        logs = self.get_queryset().order_by('-sent_at')[:10]
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data) 