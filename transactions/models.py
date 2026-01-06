from django.db import models
from users.models import User
from accounts.models import Account

# Create your models here.

# transactions/models.py
class Transaction(models.Model):
    TRANSACTION_TYPES = (
    ('ALLOCATION', 'Allocation'),
    ('PAYMENT', 'Payment'),
    ('TRANSFER', 'Transfer'),
    ('INCOME', 'Income'),
    )


    STATUS = (
    ('PENDING', 'Pending'),
    ('SUCCESS', 'Success'),
    ('FAILED', 'Failed'),
    )


    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source_account = models.ForeignKey(Account, null=True, blank=True, related_name='outgoing', on_delete=models.SET_NULL)
    destination_account = models.ForeignKey(Account, null=True, blank=True, related_name='incoming', on_delete=models.SET_NULL)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=10, choices=STATUS)
    created_at = models.DateTimeField(auto_now_add=True)