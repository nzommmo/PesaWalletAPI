from rest_framework import serializers
from categories.models import Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "category_name", "created_at")
        read_only_fields = ("id", "created_at")
