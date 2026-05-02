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

        # Validate source account belongs to the requesting user
        try:
            source_account = Account.objects.get(id=source_account_id, user=user)
        except Account.DoesNotExist:
            return Response(
                {"detail": "Source account not found or does not belong to you."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate recipient exists
        try:
            recipient = User.objects.get(phone_number=recipient_phone)
        except User.DoesNotExist:
            return Response(
                {"detail": "No user found with that phone number."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Prevent sending to yourself
        if recipient == user:
            return Response(
                {"detail": "You cannot transfer funds to yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate recipient has a primary account
        try:
            primary_recipient = recipient.accounts.get(account_type="PRIMARY")
        except Account.DoesNotExist:
            return Response(
                {"detail": f"{recipient.full_name} does not have a primary account set up yet."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate sufficient balance
        if source_account.balance < amount:
            return Response(
                {"detail": f"Insufficient funds. Available balance: {source_account.balance}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate amount is positive
        if amount <= 0:
            return Response(
                {"detail": "Transfer amount must be greater than zero."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # Deduct from source account
                source_account.balance -= amount
                source_account.save()

                # Credit recipient's primary account
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

                # Notify sender
                Notification.objects.create(
                    user=user,
                    notification_type="SUCCESS",
                    message=f"KES {amount} sent to {recipient.full_name} from {source_account.account_name}."
                )

                # Notify recipient
                Notification.objects.create(
                    user=recipient,
                    notification_type="SUCCESS",
                    message=f"You received KES {amount} from {user.full_name}."
                )

        except Exception as e:
            return Response(
                {"detail": "Transfer failed due to a server error. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            "message": f"KES {amount} sent successfully from {source_account.account_name} to {recipient.full_name}.",
            "transaction_id": txn.id
        }, status=status.HTTP_200_OK)