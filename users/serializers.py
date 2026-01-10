from rest_framework import serializers
from .models import User
from accounts.models import Account
from django.db import transaction


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "full_name",
            "phone_number",
            "email",
            "default_mpesa_number",
            "password",
        )

    def create(self, validated_data):
        password = validated_data.pop("password")

        # 🔒 Atomic: user + primary account
        with transaction.atomic():
            user = User.objects.create(**validated_data)
            user.set_password(password)
            user.save()

            # ✅ Create Primary Account automatically
            Account.objects.create(
                user=user,
                account_name="Primary Account",
                account_type="PRIMARY",
                balance=0.00,
                overspend_rule="ALLOW",
                rollover_rule="ROLLOVER",
            )

        return user

class LoginResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    phone_number = serializers.CharField()

    def to_representation(self, instance):
        phone = instance.phone_number
        masked = f"***{phone[-4:]}"
        return {
            "id": instance.id,
            "full_name": instance.full_name,
            "phone_number": masked
        }
