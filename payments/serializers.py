from rest_framework import serializers
from accounts.models import Account

class MpesaPaymentSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    to_number = serializers.CharField(max_length=20)
    payment_type = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate(self, data):
        user = self.context["request"].user

        try:
            account = Account.objects.get(
                id=data["account_id"],
                user=user
            )
        except Account.DoesNotExist:
            raise serializers.ValidationError("Invalid account")

        if data["amount"] <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")

        data["account"] = account
        return data
