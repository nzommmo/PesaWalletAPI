from rest_framework import serializers
from accounts.models import Account
from users.models import User
from .models import MpesaRequest
from transactions.models import Transaction

class TransferFundsSerializer(serializers.Serializer):
    recipient_phone = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    source_account_id = serializers.IntegerField()  # New field

    def validate_source_account_id(self, value):
        user = self.context['request'].user
        try:
            account = Account.objects.get(id=value, user=user)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Funding account does not exist or does not belong to you")
        return value

    def validate_recipient_phone(self, value):
        from users.models import User
        try:
            user = User.objects.get(phone_number=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Recipient not found")
        return value
