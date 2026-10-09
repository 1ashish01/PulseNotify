from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PriceAlert
from .serializers import PriceAlertSerializer


class PriceAlertListCreateView(generics.ListCreateAPIView):
    serializer_class = PriceAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PriceAlert.objects.filter(
            user=self.request.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PriceAlertDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        alert = get_object_or_404(
            PriceAlert,
            pk=pk,
            user=request.user,
        )

        alert.status = PriceAlert.Status.INACTIVE
        alert.save(update_fields=["status"])

        return Response(
            {"status": "inactive"},
            status=status.HTTP_200_OK,
        )
