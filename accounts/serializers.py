from rest_framework import serializers
from .models import Account
from categories.models import Category

class AccountSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True, required=True)
    category = serializers.CharField(source='category.category_name', read_only=True)

    class Meta:
        model = Account
        fields = [
            "id",
            "account_name",
            "account_type",
            "balance",
            "category_id",
            "category",
            "start_date",
            "end_date",
            "overspend_rule",
            "rollover_rule",
        ]

    def validate_category_id(self, value):
        user = self.context['request'].user
        if not Category.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError(
                "Category does not exist or does not belong to you"
            )
        return value

    def create(self, validated_data):
        category_id = validated_data.pop("category_id")
        user = self.context['request'].user
        category = Category.objects.get(id=category_id, user=user)

        # ❌ removed user=user here
        return Account.objects.create(
            category=category,
            **validated_data
        )

    def update(self, instance, validated_data):
        category_id = validated_data.pop("category_id", None)

        if category_id:
            user = self.context['request'].user
            category = Category.objects.get(id=category_id, user=user)
            instance.category = category

        return super().update(instance, validated_data)
