from django.db import models
from users.models import User

# Create your models here.

# categories/models.py
class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    category_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


def __str__(self):
    return self.category_name