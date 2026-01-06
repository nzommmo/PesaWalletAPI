from django.db import models
from users.models import User

# Create your models here.

# notifications/models.py
class Notification(models.Model):
    NOTIFICATION_TYPES = (
    ('WARN', 'Warn'),
    ('SUCCESS', 'Success'),
    ('FAILURE', 'Failure'),
    ('EXPIRY', 'Expiry'),
    ('GENERAL', 'General'),
    )


    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)