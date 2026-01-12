from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from django.db import transaction
from .models import Account
from .serializers import AccountSerializer
from transactions.models import Transaction
from notifications.models import Notification
from accounts.utils import get_primary_account
from accounts.tasks import AccountRolloverTask


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from accounts.tasks import AccountRolloverTask
        AccountRolloverTask.process_user_accounts(self.request.user)
        return Account.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if serializer.validated_data.get("account_type") == "PRIMARY":
            raise ValidationError("Primary account is created automatically")
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.instance
        if instance.account_type == "PRIMARY":
            raise ValidationError("Primary account cannot be modified")

        user = self.request.user
        primary = get_primary_account(user)

        with transaction.atomic():
            # Handle limit_amount change
            new_limit = serializer.validated_data.get("limit_amount", instance.limit_amount)
            if new_limit != instance.limit_amount:
                diff = new_limit - instance.limit_amount
                if diff > 0:
                    # Increasing limit: Deduct from primary
                    if primary.balance < diff:
                        raise ValidationError("Insufficient funds in Primary Account to increase limit")
                    primary.balance -= diff
                    instance.balance += diff
                else:
                    # Decreasing limit: Return difference to primary
                    primary.balance += abs(diff)
                    instance.balance += diff  # diff is negative
                primary.save()

            serializer.save()


def perform_destroy(self, instance):
    if instance.account_type == "PRIMARY":
        raise ValidationError("Primary account cannot be deleted")

    user = self.request.user
    primary = get_primary_account(user)

    with transaction.atomic():
        # 🔁 Return full account balance/limit to Primary
        if instance.balance > 0:
            primary.balance += instance.balance
            primary.save()

            # Log transaction
            Transaction.objects.create(
                user=user,
                source_account=instance,
                destination_account=primary,
                amount=instance.balance,
                transaction_type="TRANSFER",
                status="SUCCESS",
            )

            # Notification
            Notification.objects.create(
                user=user,
                notification_type="SUCCESS",
                message=f"{instance.balance} returned to Primary from {instance.account_name}",
            )

        instance.delete()
