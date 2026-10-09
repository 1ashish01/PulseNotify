from django.urls import path

from .views import flight_price

urlpatterns = [
    path("price/", flight_price, name="flight-price"),
]
