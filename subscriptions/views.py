from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import NotificationLog, Subscription
from .serializers import NotificationLogSerializer, SubscriptionSerializer


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).order_by("pk")

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
