from decimal import Decimal

import requests
from celery import shared_task
from django.db import transaction

from .models import NotificationLog, PriceAlert


@shared_task
def send_notification(alert_id, current_price):
    with transaction.atomic():
        try:
            alert = PriceAlert.objects.select_for_update().get(pk=alert_id)
        except PriceAlert.DoesNotExist:
            return "Alert not found."

        if alert.status != PriceAlert.Status.ACTIVE:
            return "Alert is no longer active."

        price = Decimal(str(current_price))

        if price > alert.threshold_price:
            return "Price is above the alert threshold."

        message = (
            f"Price alert for {alert.origin}-{alert.destination}: "
            f"current price is {price}, "
            f"threshold is {alert.threshold_price}."
        )

        NotificationLog.objects.create(
            alert=alert,
            triggered_price=price,
            message=message,
        )

        alert.status = PriceAlert.Status.TRIGGERED
        alert.save(update_fields=["status"])

    return "Notification recorded."


@shared_task
def check_prices():
    routes = list(
        PriceAlert.objects.filter(status=PriceAlert.Status.ACTIVE)
        .values_list("origin", "destination")
        .distinct()
    )

    queued_notifications = 0

    for origin, destination in routes:
        route = f"{origin}-{destination}"

        try:
            response = requests.get(
                "http://localhost:8000/api/flights/price/",
                params={"route": route},
                timeout=10,
            )
            response.raise_for_status()
            current_price = Decimal(str(response.json()["price"]))
        except (requests.RequestException, ValueError, KeyError):
            continue

        matching_alerts = PriceAlert.objects.filter(
            origin=origin,
            destination=destination,
            status=PriceAlert.Status.ACTIVE,
            threshold_price__gte=current_price,
        )

        for alert in matching_alerts:
            send_notification.delay(alert.id, str(current_price))
            queued_notifications += 1

    return {
        "routes_checked": len(routes),
        "notifications_queued": queued_notifications,
    }
