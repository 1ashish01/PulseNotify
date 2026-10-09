from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from alerts.models import PriceAlert

User = get_user_model()
test_usernames = ["alert_test_user1", "alert_test_user2"]

try:
    # Clean up leftovers from earlier test attempts.
    PriceAlert.objects.filter(user__username__in=test_usernames).delete()
    User.objects.filter(username__in=test_usernames).delete()

    user1 = User.objects.create_user(
        username="alert_test_user1",
        password="TestPass123!",
    )
    user2 = User.objects.create_user(
        username="alert_test_user2",
        password="TestPass123!",
    )

    client1 = APIClient()
    client2 = APIClient()

    client1.force_authenticate(user=user1)
    client2.force_authenticate(user=user2)

    host = {"HTTP_HOST": "localhost"}

    response = client1.post(
        "/api/alerts/",
        {
            "origin": "del",
            "destination": "bom",
            "threshold_price": "4500",
        },
        format="json",
        **host,
    )
    print("Create alert:", response.status_code, response.content.decode())

    response = client1.get("/api/alerts/", **host)
    print("User 1 list:", response.status_code, response.content.decode())

    response = client2.get("/api/alerts/", **host)
    print("User 2 list:", response.status_code, response.content.decode())

    response = APIClient().get("/api/alerts/", **host)
    print("Unauthenticated list:", response.status_code)

finally:
    PriceAlert.objects.filter(user__username__in=test_usernames).delete()
    User.objects.filter(username__in=test_usernames).delete()
    print("Temporary test data deleted.")
