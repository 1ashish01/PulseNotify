from django.urls import path

from .views import (
    PriceAlertDeactivateView,
    PriceAlertListCreateView,
)

urlpatterns = [
    path("", PriceAlertListCreateView.as_view(), name="alert-list-create"),
    path(
        "<int:pk>/",
        PriceAlertDeactivateView.as_view(),
        name="alert-deactivate",
    ),
]
