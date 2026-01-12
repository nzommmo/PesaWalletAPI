from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from accounts.models import Account
from .serializers import TransferFundsSerializer
from transactions.models import Transaction
from notifications.models import Notification
from users.models import User

class TransferFundsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferFundsSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        recipient_phone = serializer.validated_data['recipient_phone']
        amount = serializer.validated_data['amount']
        source_account_id = serializer.validated_data['source_account_id']

        source_account = Account.objects.get(id=source_account_id, user=user)
        recipient = User.objects.get(phone_number=recipient_phone)
        primary_recipient = recipient.accounts.get(account_type="PRIMARY")  # Recipient’s primary account

        if source_account.balance < amount:
            return Response({"detail": "Insufficient funds in the selected account"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Deduct from funding account
            source_account.balance -= amount
            source_account.save()

            # Credit recipient’s primary account
            primary_recipient.balance += amount
            primary_recipient.save()

            # Log transaction
            txn = Transaction.objects.create(
                user=user,
                source_account=source_account,
                destination_account=primary_recipient,
                amount=amount,
                transaction_type="PAYMENT",
                status="SUCCESS"
            )

            # Notifications
            Notification.objects.create(
                user=user,
                notification_type="SUCCESS",
                message=f"{amount} sent to {recipient.full_name} from {source_account.account_name}"
            )
            Notification.objects.create(
                user=recipient,
                notification_type="SUCCESS",
                message=f"You received {amount} from {user.full_name}"
            )

        return Response({
            "message": f"{amount} sent successfully from {source_account.account_name} to {recipient.full_name}",
            "transaction_id": txn.id
        }, status=status.HTTP_200_OK)
