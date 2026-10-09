from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from alerts.models import PriceAlert

User = get_user_model()
names = ["deactivate_test_user1", "deactivate_test_user2"]

try:
    PriceAlert.objects.filter(user__username__in=names).delete()
    User.objects.filter(username__in=names).delete()

    user1 = User.objects.create_user(
        username=names[0], password="TestPass123!"
    )
    user2 = User.objects.create_user(
        username=names[1], password="TestPass123!"
    )

    alert = PriceAlert.objects.create(
        user=user1,
        origin="DEL",
        destination="BOM",
        threshold_price="4500.00",
    )

    client1 = APIClient()
    client2 = APIClient()
    client1.force_authenticate(user=user1)
    client2.force_authenticate(user=user2)
    host = {"HTTP_HOST": "localhost"}

    response = client1.delete(
        f"/api/alerts/{alert.pk}/", **host
    )
    print("Owner deactivation:", response.status_code, response.content.decode())

    alert.refresh_from_db()
    print("Database record still exists:", PriceAlert.objects.filter(pk=alert.pk).exists())
    print("Stored status:", alert.status)

    response = client2.delete(
        f"/api/alerts/{alert.pk}/", **host
    )
    print("Other user deactivation:", response.status_code)

    response = client1.delete(
        "/api/alerts/999999/", **host
    )
    print("Nonexistent alert:", response.status_code)

finally:
    PriceAlert.objects.filter(user__username__in=names).delete()
    User.objects.filter(username__in=names).delete()
    print("Temporary test data deleted.")
