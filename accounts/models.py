from django.db import models
from users.models import User
from categories.models import Category

# Create your models here.

# accounts/models.py
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
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    overspend_rule = models.CharField(max_length=10, choices=OVERSPEND_RULES, default='BLOCK')
    rollover_rule = models.CharField(max_length=15, choices=ROLLOVER_RULES, default='ROLLOVER')
    is_expired = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


def __str__(self):
    return self.account_name