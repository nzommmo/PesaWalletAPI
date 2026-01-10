from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from decimal import Decimal
from transactions.models import Transaction
from notifications.models import Notification
from transactions.serializers import AllocateFundsSerializer,TopUpSerializer
from accounts.models import Account

class AllocateFundsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AllocateFundsSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        source = serializer.validated_data["source"]
        destination = serializer.validated_data["destination"]
        amount = serializer.validated_data["amount"]

        # 🔐 Overspend enforcement
        if source.balance < amount:
            if source.overspend_rule == "BLOCK":
                return Response(
                    {"error": "Insufficient funds"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if source.overspend_rule == "WARN":
                Notification.objects.create(
                    user=request.user,
                    notification_type="WARN",
                    message=f"Overspending {amount} from {source.account_name}"
                )

        # 💰 Atomic money debugging protection
        with transaction.atomic():
            source.balance -= amount
            destination.balance += amount
            source.save()
            destination.save()

            Transaction.objects.create(
                user=request.user,
                source_account=source,
                destination_account=destination,
                amount=amount,
                transaction_type="ALLOCATION",
                status="SUCCESS"
            )

            Notification.objects.create(
                user=request.user,
                notification_type="SUCCESS",
                message=f"{amount} transferred to {destination.account_name}"
            )

        return Response(
            {"message": "Funds allocated successfully"},
            status=status.HTTP_200_OK
        )


class TopUpView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TopUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]

        try:
            primary = Account.objects.get(
                user=request.user,
                account_type="PRIMARY"
            )
        except Account.DoesNotExist:
            return Response(
                {"error": "Primary account not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            primary.balance += amount
            primary.save()

            Transaction.objects.create(
                user=request.user,
                destination_account=primary,
                amount=amount,
                transaction_type="INCOME",
                status="SUCCESS"
            )

            Notification.objects.create(
                user=request.user,
                notification_type="SUCCESS",
                message=f"{amount} added to Primary Account"
            )

        return Response(
            {"message": "Top-up successful"},
            status=status.HTTP_200_OK
        )