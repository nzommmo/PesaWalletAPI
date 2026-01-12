from django.db import models
from users.models import User
from categories.models import Category

# -------------------------
# Account Model
# -------------------------
class Account(models.Model):
    ACCOUNT_TYPES = (
        ('PRIMARY', 'Primary'),
        ('DIGITAL', 'Digital'),
        ('SAVINGS', 'Savings'),
    )

    OVERSPEND_RULES = (
        ('BLOCK', 'Block'),
        ('WARN', 'Warn'),
        ('ALLOW', 'Allow'),
    )

    ROLLOVER_RULES = (
        ('ROLLOVER', 'Rollover'),
        ('RETURN', 'Return'),
        ('REALLOCATE', 'Reallocate'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    limit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    overspend_rule = models.CharField(max_length=10, choices=OVERSPEND_RULES, default='BLOCK')
    rollover_rule = models.CharField(max_length=15, choices=ROLLOVER_RULES, default='ROLLOVER')
    is_expired = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.account_name

    @property
    def health_percentage(self):
        """Return account health as a percentage of balance vs limit"""
        if self.limit_amount == 0:
            return 100
        return float(self.balance) / float(self.limit_amount) * 100

# -------------------------
# Wallet Model
# -------------------------
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.phone_number} - {self.balance}"
