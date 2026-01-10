from rest_framework import serializers
from .models import Account

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = (
            "id",
            "account_name",
            "account_type",
            "category",
            "balance",
            "start_date",
            "end_date",
            "overspend_rule",
            "rollover_rule",
            "created_at",
        )
        read_only_fields = ("id", "account_type", "balance", "created_at")

    def validate_category(self, category):
        user = self.context["request"].user

        if category and category.user != user:
            raise serializers.ValidationError("Invalid category")

        return category

    def create(self, validated_data):
        user = self.context["request"].user

        return Account.objects.create(
            user=user,
            account_type="DIGITAL",
            balance=0.00,
            **validated_data
        )