from django.db import models
from users.models import User

class Income(models.Model):
    FREQUENCY_CHOICES = (
        ("DAILY", "Daily"),
        ("WEEKLY", "Weekly"),
        ("FORTNIGHT", "Fortnight"),
        ("MONTHLY", "Monthly"),
        ("ONE_OFF", "One Off"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="incomes")
    source_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source_name} ({self.amount})"
