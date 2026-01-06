from django.db import models
from users.models import User
from transactions.models import Transaction

# Create your models here.

# payments/models.py
class MpesaRequest(models.Model):
    STATUS = (
    ('PENDING', 'Pending'),
    ('SUCCESS', 'Success'),
    ('FAILED', 'Failed'),
    )


    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
    from_number = models.CharField(max_length=20)
    to_number = models.CharField(max_length=20)
    payment_type = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)