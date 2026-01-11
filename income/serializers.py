from rest_framework import serializers
from .models import Income

from rest_framework import serializers
from .models import Income

class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = (
            "id",
            "source_name",
            "amount",
            "frequency",
            "description",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "created_at")



class PrimaryTopUpSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    description = serializers.CharField()
