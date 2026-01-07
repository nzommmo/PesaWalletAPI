from rest_framework import serializers
from .models import Account

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = (
            'id',
            'account_name',
            'account_type',
            'category',
            'balance',
            'start_date',
            'end_date',
            'overspend_rule',
            'rollover_rule',
            'is_expired',
            'created_at',
        )
        read_only_fields = ('balance', 'is_expired', 'created_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
