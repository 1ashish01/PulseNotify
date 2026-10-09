
from django.db.models import Count, Q

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import IsAdminUser
from alerts.models import NotificationLog, PriceAlert


@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_summary(request):
    alert_metrics = PriceAlert.objects.aggregate(
        total_alerts=Count("id"),
        active_alerts=Count(
            "id",
            filter=Q(status=PriceAlert.Status.ACTIVE),
        ),
        triggered_alerts=Count(
            "id",
            filter=Q(status=PriceAlert.Status.TRIGGERED),
        ),
    )

    total_notifications = NotificationLog.objects.aggregate(
        total=Count("id")
    )["total"]

    top_routes = list(
        PriceAlert.objects.values("origin", "destination")
        .annotate(alert_count=Count("id"))
        .order_by("-alert_count", "origin", "destination")[:5]
    )

    return Response(
        {
            "total_alerts": alert_metrics["total_alerts"],
            "active_alerts": alert_metrics["active_alerts"],
            "triggered_alerts": alert_metrics["triggered_alerts"],
            "total_notifications": total_notifications,
            "top_routes": top_routes,
        },
        status=status.HTTP_200_OK,
    )