from django.contrib import admin
from django.urls import include, path

from accounts.admin_views import admin_summary

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/flights/", include("flights.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/alerts/", include("alerts.urls")),
    path("api/admin/summary/", admin_summary, name="admin-summary"),
]
