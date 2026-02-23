# serializers.py
from rest_framework import serializers
from .models import User
from accounts.models import Account
from django.db import transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


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

        with transaction.atomic():
            user = User.objects.create(**validated_data)
            user.set_password(password)
            user.save()

            Account.objects.create(
                user=user,
                account_name="Primary Account",
                account_type="PRIMARY",
                balance=0.00,
                overspend_rule="ALLOW",
                rollover_rule="ROLLOVER",
            )

        return user


# ✅ Custom JWT serializer — bakes is_superadmin into the token
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["is_superadmin"] = user.is_superadmin  # ← added to JWT payload
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # ✅ Also include is_superadmin in the login response body
        data["user"] = LoginResponseSerializer(self.user).data

        return data


class LoginResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    phone_number = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    is_superadmin = serializers.BooleanField()  # ← added

    def to_representation(self, instance):
        phone = instance.phone_number
        masked = f"***{phone[-4:]}" if phone else None

        return {
            "id": instance.id,
            "full_name": instance.full_name,
            "phone_number": masked,
            "email": instance.email,
            "is_superadmin": instance.is_superadmin,  # ← added
        }