from rest_framework import serializers

from .models import PriceAlert


class PriceAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceAlert
        fields = [
            "id",
            "origin",
            "destination",
            "threshold_price",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]

    def validate_origin(self, value):
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise serializers.ValidationError(
                "Origin must be a three-letter airport code."
            )
        return value

    def validate_destination(self, value):
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise serializers.ValidationError(
                "Destination must be a three-letter airport code."
            )
        return value

    def validate_threshold_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Threshold price must be greater than zero."
            )
        return value
