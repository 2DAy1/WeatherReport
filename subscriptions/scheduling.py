from collections import defaultdict
from collections.abc import Callable
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Subscription


def schedule_due_notifications(
    publish: Callable[[int, list[int]], None],
) -> int:
    now = timezone.now()
    due = Subscription.objects.filter(is_active=True, next_run_at__lte=now)

    with transaction.atomic():
        subscriptions = list(due.select_for_update(skip_locked=True).order_by("pk"))
        by_city: dict[int, list[int]] = defaultdict(list)
        for subscription in subscriptions:
            by_city[subscription.city_id].append(subscription.pk)
            subscription.next_run_at = now + timedelta(hours=subscription.notification_period)

        for city_id, subscription_ids in by_city.items():
            publish(city_id, subscription_ids)

        Subscription.objects.bulk_update(subscriptions, ["next_run_at"])
    return len(subscriptions)
