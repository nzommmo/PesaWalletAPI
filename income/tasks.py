from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from .models import Income
from transactions.models import Transaction
from notifications.models import Notification
from accounts.utils import get_primary_account


class IncomeTaskManager:
    """
    Applies scheduled income to Primary Account
    """

    FREQUENCY_DAYS = {
        "DAILY": 1,
        "WEEKLY": 7,
        "FORTNIGHT": 14,
        "MONTHLY": 30,   # simple & predictable
    }

    @staticmethod
    def is_due(income: Income):
        today = timezone.now().date()

        if not income.is_active:
            return False

        if income.frequency == "ONE_OFF":
            return income.last_applied is None

        if income.last_applied is None:
            return True

        delta_days = IncomeTaskManager.FREQUENCY_DAYS.get(income.frequency)
        return (today - income.last_applied).days >= delta_days

    @staticmethod
    def apply_income(income: Income):
        user = income.user
        primary = get_primary_account(user)

        with transaction.atomic():
            primary.balance += income.amount
            primary.save()

            Transaction.objects.create(
                user=user,
                destination_account=primary,
                amount=income.amount,
                transaction_type="INCOME",
                status="SUCCESS",
            )

            Notification.objects.create(
                user=user,
                notification_type="SUCCESS",
                message=f"{income.amount} credited from {income.source_name}",
            )

            income.last_applied = timezone.now().date()

            if income.frequency == "ONE_OFF":
                income.is_active = False

            income.save()

    @staticmethod
    def process_user_incomes(user):
        incomes = Income.objects.filter(user=user, is_active=True)

        for income in incomes:
            if IncomeTaskManager.is_due(income):
                IncomeTaskManager.apply_income(income)
