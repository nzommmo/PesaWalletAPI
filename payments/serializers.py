from rest_framework import serializers
from .models import MpesaRequest

class MpesaRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaRequest
        fields = (
            'id',
            'from_number',
            'to_number',
            'payment_type',
            'amount',
            'status',
            'created_at',
        )
        read_only_fields = ('status', 'created_at')
