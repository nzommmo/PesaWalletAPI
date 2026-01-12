from django.utils import timezone
from django.db import transaction

from .models import Account
from transactions.models import Transaction
from notifications.models import Notification
from accounts.utils import get_primary_account


class AccountRolloverTask:
    """
    Handles expiry logic for accounts:
    - ROLLOVER
    - RETURN
    - REALLOCATE (notify only for now)
    """

    @staticmethod
    def process_account(account: Account):
        # Skip if no expiry or already expired
        if not account.end_date or account.is_expired:
            return

        today = timezone.now().date()
        if today <= account.end_date:
            return

        with transaction.atomic():
            user = account.user
            balance = account.balance

            if balance > 0:
                if account.rollover_rule == "RETURN":
                    primary = get_primary_account(user)
                    primary.balance += balance
                    primary.save()

                    Transaction.objects.create(
                        user=user,
                        source_account=account,
                        destination_account=primary,
                        amount=balance,
                        transaction_type="TRANSFER",
                        status="SUCCESS",
                    )

                    Notification.objects.create(
                        user=user,
                        notification_type="SUCCESS",
                        message=f"{balance} returned to Primary from expired {account.account_name}",
                    )

                    account.balance = 0

                elif account.rollover_rule == "ROLLOVER":
                    # Carry forward → just keep balance
                    Notification.objects.create(
                        user=user,
                        notification_type="GENERAL",
                        message=f"{account.account_name} rolled over with balance {balance}",
                    )

                elif account.rollover_rule == "REALLOCATE":
                    # Manual user decision
                    Notification.objects.create(
                        user=user,
                        notification_type="EXPIRY",
                        message=f"{account.account_name} expired with {balance}. Please reallocate funds.",
                    )

            account.is_expired = True
            account.save()

    @staticmethod
    def process_user_accounts(user):
        accounts = Account.objects.filter(
            user=user,
            is_expired=False,
            end_date__isnull=False,
        )

        for account in accounts:
            AccountRolloverTask.process_account(account)
