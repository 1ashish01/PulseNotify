from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.models import UserProfile
from alerts.models import PriceAlert, NotificationLog

User = get_user_model()
names = ["summary_test_admin", "summary_test_user"]

try:
    User.objects.filter(username__in=names).delete()

    admin_user = User.objects.create_user(
        username=names[0],
        password="TestPass123!",
    )
    regular_user = User.objects.create_user(
        username=names[1],
        password="TestPass123!",
    )

    admin_user.profile.role = UserProfile.Role.ADMIN
    admin_user.profile.save()

    alert = PriceAlert.objects.create(
        user=regular_user,
        origin="DEL",
        destination="BOM",
        threshold_price="4500.00",
    )

    NotificationLog.objects.create(
        alert=alert,
        triggered_price="4200.00",
        message="Test notification",
    )

    admin_client = APIClient()
    user_client = APIClient()
    admin_client.force_authenticate(user=admin_user)
    user_client.force_authenticate(user=regular_user)

    host = {"HTTP_HOST": "localhost"}

    response = admin_client.get("/api/admin/summary/", **host)
    print("Admin access:", response.status_code)
    print("Summary response:", response.content.decode())

    response = user_client.get("/api/admin/summary/", **host)
    print("Regular user access:", response.status_code)
    print("Regular user response:", response.content.decode())

finally:
    User.objects.filter(username__in=names).delete()
    print("Temporary test users and their related data cleaned up.")
