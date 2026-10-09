from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from alerts.models import NotificationLog, PriceAlert
from alerts.tasks import check_prices, send_notification


User = get_user_model()


class SendNotificationTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notification_test_user",
            password="TestPass123!",
        )
        self.alert = PriceAlert.objects.create(
            user=self.user,
            origin="DEL",
            destination="BOM",
            threshold_price="4000.00",
        )

    def test_price_below_threshold_creates_notification(self):
        result = send_notification.run(self.alert.id, "3999.00")

        self.alert.refresh_from_db()
        self.assertEqual(result, "Notification recorded.")
        self.assertEqual(self.alert.status, PriceAlert.Status.TRIGGERED)
        self.assertEqual(NotificationLog.objects.filter(alert=self.alert).count(), 1)
        self.assertEqual(
            NotificationLog.objects.get(alert=self.alert).triggered_price,
            3999,
        )

    def test_price_equal_to_threshold_creates_notification(self):
        result = send_notification.run(self.alert.id, "4000.00")

        self.alert.refresh_from_db()
        self.assertEqual(result, "Notification recorded.")
        self.assertEqual(self.alert.status, PriceAlert.Status.TRIGGERED)
        self.assertEqual(NotificationLog.objects.filter(alert=self.alert).count(), 1)

    def test_price_above_threshold_does_not_create_notification(self):
        result = send_notification.run(self.alert.id, "4001.00")

        self.alert.refresh_from_db()
        self.assertEqual(result, "Price is above the alert threshold.")
        self.assertEqual(self.alert.status, PriceAlert.Status.ACTIVE)
        self.assertEqual(NotificationLog.objects.filter(alert=self.alert).count(), 0)

    def test_triggered_alert_does_not_create_duplicate_notification(self):
        send_notification.run(self.alert.id, "3900.00")
        result = send_notification.run(self.alert.id, "3800.00")

        self.assertEqual(result, "Alert is no longer active.")
        self.assertEqual(NotificationLog.objects.filter(alert=self.alert).count(), 1)


class CheckPricesTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="price_check_test_user",
            password="TestPass123!",
        )
        self.matching_alert = PriceAlert.objects.create(
            user=self.user,
            origin="DEL",
            destination="BOM",
            threshold_price="4500.00",
        )
        PriceAlert.objects.create(
            user=self.user,
            origin="DEL",
            destination="BOM",
            threshold_price="3000.00",
        )
        PriceAlert.objects.create(
            user=self.user,
            origin="BLR",
            destination="HYD",
            threshold_price="2500.00",
        )

    @patch("alerts.tasks.send_notification.delay")
    @patch("alerts.tasks.requests.get")
    def test_checks_distinct_routes_and_queues_matching_alerts(
        self, mock_get, mock_delay
    ):
        mock_response = Mock()
        mock_response.json.return_value = {"price": 4000}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = check_prices.run()

        self.assertEqual(result["routes_checked"], 2)
        self.assertEqual(result["notifications_queued"], 1)
        self.assertEqual(mock_get.call_count, 2)
        mock_delay.assert_called_once_with(self.matching_alert.id, "4000")

    @patch("alerts.tasks.send_notification.delay")
    @patch("alerts.tasks.requests.get")
    def test_failed_route_request_does_not_queue_notifications(
        self, mock_get, mock_delay
    ):
        import requests

        mock_get.side_effect = requests.RequestException("Test connection failure")

        result = check_prices.run()

        self.assertEqual(result["routes_checked"], 2)
        self.assertEqual(result["notifications_queued"], 0)
        mock_delay.assert_not_called()


class AlertScopingTests(TestCase):
    def test_user_only_sees_their_own_alerts(self):
        user1 = User.objects.create_user(
            username="scope_test_user1",
            password="TestPass123!",
        )
        user2 = User.objects.create_user(
            username="scope_test_user2",
            password="TestPass123!",
        )

        PriceAlert.objects.create(
            user=user1,
            origin="DEL",
            destination="BOM",
            threshold_price="4500.00",
        )

        client = APIClient()
        client.force_authenticate(user=user2)
        response = client.get("/api/alerts/", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

class NotificationLogTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notification_log_fields_user",
            password="TestPass123!",
        )
        self.alert = PriceAlert.objects.create(
            user=self.user,
            origin="DEL",
            destination="BOM",
            threshold_price="4500.00",
        )

    def test_notification_records_price_message_and_timestamp(self):
        send_notification.run(self.alert.id, "4200.00")

        notification = NotificationLog.objects.get(alert=self.alert)

        self.assertEqual(notification.triggered_price, 4200)
        self.assertIn("DEL-BOM", notification.message)
        self.assertIn("4200", notification.message)
        self.assertIn("4500.00", notification.message)
        self.assertIsNotNone(notification.notified_at)


class AlertApiAuthorizationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="alert_owner_regression",
            password="TestPass123!",
        )
        self.other_user = User.objects.create_user(
            username="alert_other_regression",
            password="TestPass123!",
        )
        self.alert = PriceAlert.objects.create(
            user=self.owner,
            origin="DEL",
            destination="BOM",
            threshold_price="4500.00",
        )
        self.host = {"HTTP_HOST": "localhost"}

    def test_unauthenticated_user_cannot_list_alerts(self):
        response = APIClient().get("/api/alerts/", **self.host)

        self.assertEqual(response.status_code, 401)

    def test_other_user_cannot_deactivate_alert(self):
        client = APIClient()
        client.force_authenticate(user=self.other_user)

        response = client.delete(
            f"/api/alerts/{self.alert.pk}/",
            **self.host,
        )

        self.assertEqual(response.status_code, 404)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, PriceAlert.Status.ACTIVE)

    def test_owner_can_deactivate_alert_without_deleting_it(self):
        client = APIClient()
        client.force_authenticate(user=self.owner)

        response = client.delete(
            f"/api/alerts/{self.alert.pk}/",
            **self.host,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"status": "inactive"})
        self.assertTrue(PriceAlert.objects.filter(pk=self.alert.pk).exists())
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, PriceAlert.Status.INACTIVE)


class AdminSummaryAuthorizationTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="summary_admin_regression",
            password="TestPass123!",
        )
        self.regular_user = User.objects.create_user(
            username="summary_regular_regression",
            password="TestPass123!",
        )
        self.admin_user.profile.role = "admin"
        self.admin_user.profile.save(update_fields=["role"])
        self.host = {"HTTP_HOST": "localhost"}

    def test_regular_user_is_forbidden_from_admin_summary(self):
        client = APIClient()
        client.force_authenticate(user=self.regular_user)

        response = client.get("/api/admin/summary/", **self.host)

        self.assertEqual(response.status_code, 403)

    def test_admin_user_can_access_admin_summary(self):
        client = APIClient()
        client.force_authenticate(user=self.admin_user)

        response = client.get("/api/admin/summary/", **self.host)

        self.assertEqual(response.status_code, 200)
        self.assertIn("total_alerts", response.data)
        self.assertIn("total_notifications", response.data)
        self.assertIn("top_routes", response.data)
