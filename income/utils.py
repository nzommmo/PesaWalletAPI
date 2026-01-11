from datetime import timedelta
from django.utils import timezone

FREQUENCY_DAYS = {
    "DAILY": 1,
    "WEEKLY": 7,
    "FORTNIGHT": 14,
    "MONTHLY": 30,
}


def get_next_run_date(income):
    today = timezone.now().date()

    if not income.is_active:
        return None

    if income.frequency == "ONE_OFF":
        return None if income.last_applied else today

    if income.last_applied:
        return income.last_applied + timedelta(days=FREQUENCY_DAYS[income.frequency])

    return today
