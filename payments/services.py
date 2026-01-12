from django.db import transaction
from rest_framework.exceptions import ValidationError

from accounts.utils import get_primary_account
from transactions.models import Transaction
from notifications.models import Notification


def transfer_funds(sender, recipient, amount):
    if sender == recipient:
        raise ValidationError("You cannot send money to yourself")

    with transaction.atomic():
        sender_primary = get_primary_account(sender)
        recipient_primary = get_primary_account(recipient)

        if sender_primary.balance < amount:
            raise ValidationError("Insufficient balance")

        sender_primary.balance -= amount
        recipient_primary.balance += amount

        sender_primary.save()
        recipient_primary.save()

        Transaction.objects.create(
            user=sender,
            source_account=sender_primary,
            destination_account=recipient_primary,
            amount=amount,
            transaction_type="TRANSFER",
            status="SUCCESS",
        )

        Notification.objects.create(
            user=sender,
            notification_type="SUCCESS",
            message=f"You sent {amount} to {recipient.phone_number}",
        )

        Notification.objects.create(
            user=recipient,
            notification_type="SUCCESS",
            message=f"You received {amount} from {sender.phone_number}",
        )
