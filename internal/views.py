from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count

from users.models import User
from accounts.models import Account
from transactions.models import Transaction


class AdminOverviewView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        last_24_hours = timezone.now() - timedelta(hours=24)

        total_users = User.objects.count()
        total_accounts = Account.objects.count()
        total_transactions = Transaction.objects.count()

        total_volume = Transaction.objects.filter(
            status="SUCCESS"
        ).aggregate(total=Sum("amount"))["total"] or 0

        last_24hr_volume = Transaction.objects.filter(
            status="SUCCESS",
            created_at__gte=last_24_hours
        ).aggregate(total=Sum("amount"))["total"] or 0

        payments = Transaction.objects.filter(
            transaction_type="PAYMENT"
        ).values("status").annotate(count=Count("id"))

        return Response({
            "total_users": total_users,
            "total_accounts": total_accounts,
            "total_transactions": total_transactions,
            "total_success_volume": total_volume,
            "last_24hr_volume": last_24hr_volume,
            "payment_breakdown": payments
        })

class AdminUsersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all()

        data = []

        for user in users:
            accounts = Account.objects.filter(user=user)
            total_balance = sum(a.balance for a in accounts)

            data.append({
                "user_id": user.id,
                "email": user.email,
                "phone": user.phone_number,
                "accounts_count": accounts.count(),
                "total_balance": total_balance
            })

        return Response(data)

class AdminTransactionsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        transactions = Transaction.objects.all().order_by("-created_at")

        txn_type = request.GET.get("type")
        status = request.GET.get("status")

        if txn_type:
            transactions = transactions.filter(transaction_type=txn_type)

        if status:
            transactions = transactions.filter(status=status)

        data = [
            {
                "id": t.id,
                "user": t.user.email,
                "type": t.transaction_type,
                "amount": t.amount,
                "status": t.status,
                "created_at": t.created_at
            }
            for t in transactions[:200]
        ]

        return Response(data)