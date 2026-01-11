from rest_framework import serializers
from .models import Income

from rest_framework import serializers
from .models import Income

from rest_framework import serializers
from .models import Income
from .utils import get_next_run_date


class IncomeSerializer(serializers.ModelSerializer):
    next_run_date = serializers.SerializerMethodField()

    class Meta:
        model = Income
        fields = [
            "id",
            "source_name",
            "amount",
            "frequency",
            "description",
            "is_active",
            "last_applied",
            "next_run_date",
            "created_at",
        ]

    def get_next_run_date(self, obj):
        return get_next_run_date(obj)




class PrimaryTopUpSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    description = serializers.CharField()
