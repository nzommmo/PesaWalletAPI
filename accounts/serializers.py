from rest_framework import serializers
from .models import Account
from categories.models import Category

class AccountSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True, required=True)
    category = serializers.CharField(source='category.category_name', read_only=True)
    health_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            "id",
            "account_name",
            "account_type",
            "balance",
            "limit_amount",
            "health_percentage",   # New field
            "category_id",
            "category",
            "start_date",
            "end_date",
            "overspend_rule",
            "rollover_rule",
        ]

    def get_health_percentage(self, obj):
        if obj.limit_amount > 0:
            return round((obj.balance / obj.limit_amount) * 100, 2)
        return 0

    def create(self, validated_data):
        limit_amount = validated_data.pop("limit_amount", 0)
        category_id = validated_data.pop("category_id")
        user = self.context['request'].user
        category = Category.objects.get(id=category_id, user=user)

        # Remove user and balance if they exist in validated_data
        validated_data.pop('user', None)
        validated_data.pop('balance', None)

        from accounts.utils import get_primary_account
        primary = get_primary_account(user)

        if primary.balance < limit_amount:
            raise serializers.ValidationError("Insufficient funds in Primary Account to set this limit")

        # Deduct the limit from primary
        primary.balance -= limit_amount
        primary.save()

        account = Account.objects.create(
            user=user,
            category=category,
            limit_amount=limit_amount,
            balance=limit_amount,  # Start balance = limit
            **validated_data
        )

        # Log transaction and notification
        from transactions.models import Transaction
        from notifications.models import Notification

        Transaction.objects.create(
            user=user,
            source_account=primary,
            destination_account=account,
            amount=limit_amount,
            transaction_type="TRANSFER",
            status="SUCCESS",
        )

        Notification.objects.create(
            user=user,
            notification_type="SUCCESS",
            message=f"{limit_amount} allocated to {account.account_name} from Primary Account"
        )

        return account
