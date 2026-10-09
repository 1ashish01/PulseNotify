
import random

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


FLIGHT_ROUTES = {
    "DEL-BOM": (3000, 7000),
    "BLR-HYD": (1500, 4000),
    "DEL-BLR": (4000, 9000),
    "BOM-GOA": (2000, 5000),
}


@api_view(["GET"])
@permission_classes([AllowAny])
def flight_price(request):
    route = request.query_params.get("route", "").strip().upper()

    if route not in FLIGHT_ROUTES:
        return Response(
            {"error": "Unknown route.", "route": route},
            status=404,
        )

    minimum_price, maximum_price = FLIGHT_ROUTES[route]
    current_price = random.randint(minimum_price, maximum_price)

    return Response({
        "route": route,
        "price": current_price,
    })