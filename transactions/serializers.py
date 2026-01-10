from rest_framework import serializers
from .models import Transaction,Account

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            'id',
            'transaction_type',
            'source_account',
            'destination_account',
            'amount',
            'status',
            'created_at',
        )


class AllocateFundsSerializer(serializers.Serializer):
    source_account = serializers.IntegerField()
    destination_account = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate(self, data):
        user = self.context["request"].user

        try:
            source = Account.objects.get(id=data["source_account"], user=user)
            destination = Account.objects.get(id=data["destination_account"], user=user)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Invalid account")

        if source.id == destination.id:
            raise serializers.ValidationError("Cannot allocate to the same account")

        if data["amount"] <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")

        data["source"] = source
        data["destination"] = destination
        return data



class TopUpSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
