from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from transactions.models import Transaction
from payments.models import MpesaRequest
from notifications.models import Notification
from payments.serializers import MpesaPaymentSerializer

class MpesaPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MpesaPaymentSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        account = serializer.validated_data["account"]
        amount = serializer.validated_data["amount"]

        # 🔐 Overspend enforcement
        if account.balance < amount:
            if account.overspend_rule == "BLOCK":
                return Response(
                    {"error": "Insufficient funds"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if account.overspend_rule == "WARN":
                Notification.objects.create(
                    user=request.user,
                    notification_type="WARN",
                    message=f"Overspending {amount} from {account.account_name}"
                )

        with transaction.atomic():
            txn = Transaction.objects.create(
                user=request.user,
                source_account=account,
                amount=amount,
                transaction_type="PAYMENT",
                status="PENDING"
            )

            MpesaRequest.objects.create(
                user=request.user,
                transaction=txn,
                from_number=request.user.default_mpesa_number,
                to_number=serializer.validated_data["to_number"],
                payment_type=serializer.validated_data["payment_type"],
                amount=amount,
                status="PENDING"
            )

        return Response(
            {"message": "STK Push sent. Awaiting confirmation."},
            status=status.HTTP_200_OK
        )


class MpesaCallbackView(APIView):
    permission_classes = []

    def post(self, request):
        transaction_id = request.data.get("transaction_id")
        success = request.data.get("success")

        try:
            txn = Transaction.objects.select_related(
                "source_account"
            ).get(id=transaction_id)
        except Transaction.DoesNotExist:
            return Response(
                {"error": "Invalid transaction"},
                status=status.HTTP_404_NOT_FOUND
            )

        if txn.status != "PENDING":
            return Response(
                {"error": "Transaction already processed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        account = txn.source_account

        with transaction.atomic():
            if success:
                account.balance -= txn.amount
                account.save()

                txn.status = "SUCCESS"
                txn.save()

                Notification.objects.create(
                    user=txn.user,
                    notification_type="SUCCESS",
                    message=f"Payment of {txn.amount} successful"
                )
            else:
                txn.status = "FAILED"
                txn.save()

                Notification.objects.create(
                    user=txn.user,
                    notification_type="FAILURE",
                    message=f"Payment of {txn.amount} failed"
                )

        return Response(
            {"message": "Callback processed"},
            status=status.HTTP_200_OK
        )
