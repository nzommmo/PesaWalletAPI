from rest_framework import serializers
from .models import User
from accounts.models import Account

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            'full_name',
            'phone_number',
            'email',
            'password',
            'default_mpesa_number',
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        # Create Primary Account automatically
        Account.objects.create(
            user=user,
            account_name="Primary Account",
            account_type="PRIMARY",
            balance=0.00
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
