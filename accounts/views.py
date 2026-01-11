from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from django.db import transaction

from .models import Account
from .serializers import AccountSerializer
from transactions.models import Transaction
from notifications.models import Notification
from accounts.utils import get_primary_account


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if serializer.validated_data.get("account_type") == "PRIMARY":
            raise ValidationError("Primary account is created automatically")
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.account_type == "PRIMARY":
            raise ValidationError("Primary account cannot be modified")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.account_type == "PRIMARY":
            raise ValidationError("Primary account cannot be deleted")

        user = self.request.user

        with transaction.atomic():
            # 🔁 Return balance to Primary
            if instance.balance > 0:
                primary = get_primary_account(user)
                primary.balance += instance.balance
                primary.save()

                Transaction.objects.create(
                    user=user,
                    source_account=instance,
                    destination_account=primary,
                    amount=instance.balance,
                    transaction_type="TRANSFER",
                    status="SUCCESS",
                )

                Notification.objects.create(
                    user=user,
                    notification_type="SUCCESS",
                    message=f"{instance.balance} returned to Primary from {instance.account_name}",
                )

            instance.delete()
