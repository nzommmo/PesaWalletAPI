from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from django.db import transaction
from .models import Account
from .serializers import AccountSerializer
from transactions.models import Transaction
from notifications.models import Notification
from accounts.utils import get_primary_account
from accounts.tasks import AccountRolloverTask
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from collections import defaultdict   
from rest_framework.decorators import action   


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        AccountRolloverTask.process_user_accounts(self.request.user)
        return Account.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if serializer.validated_data.get("account_type") == "PRIMARY":
            raise ValidationError("Primary account is created automatically")
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user
        primary = get_primary_account(user)
        validated = serializer.validated_data

        with transaction.atomic():
            # ── Rename: allowed on all accounts including PRIMARY ──
            # (serializer.save() handles this automatically)

            # ── Category change: allowed on all non-PRIMARY accounts ──
            if "category_id" in validated and instance.account_type == "PRIMARY":
                raise ValidationError("Primary account cannot have a category")

            if "category_id" in validated:
                from categories.models import Category
                category = Category.objects.get(
                    id=validated.pop("category_id"), user=user
                )
                instance.category = category

            # ── Limit change: only on non-PRIMARY accounts ──
            new_limit = validated.get("limit_amount")
            if new_limit is not None and new_limit != instance.limit_amount:
                if instance.account_type == "PRIMARY":
                    raise ValidationError("Primary account limit cannot be changed")

                diff = new_limit - instance.limit_amount
                if diff > 0:
                    if primary.balance < diff:
                        raise ValidationError(
                            "Insufficient funds in Primary Account to increase limit"
                        )
                    primary.balance -= diff
                    instance.balance += diff
                else:
                    primary.balance += abs(diff)
                    instance.balance += diff  # diff is negative
                primary.save()

            serializer.save(category=instance.category)

    def perform_destroy(self, instance):          # ← fixed: inside the class
        if instance.account_type == "PRIMARY":
            raise ValidationError("Primary account cannot be deleted")

        user = self.request.user
        primary = get_primary_account(user)

        with transaction.atomic():
            if instance.balance > 0:
                primary.balance += instance.balance
                primary.save()

                Transaction.objects.create(
                    user=user,
                    source_account=instance,
                    destination_account=primary,
                    amount=instance.balance,
                    transaction_type="TRANSFER",
                    status="SUCCESS",
                )

                Notification.objects.create(
                    user=user,
                    notification_type="SUCCESS",
                    message=f"{instance.balance} returned to Primary from {instance.account_name}",
                )

            instance.delete()
    
    @action(detail=False, methods=["get"], url_path="category-insights")
    def category_insights(self, request):
        user = request.user

        # Get all PAYMENT transactions (spending)
        transactions = Transaction.objects.filter(
            user=user,
            transaction_type="PAYMENT",
            status="SUCCESS",
            source_account__category__isnull=False
        ).select_related("source_account__category")

        category_data = defaultdict(lambda: {
            "total_spent": 0,
            "transactions": 0
        })

        total_spending = 0

        for txn in transactions:
            category = txn.source_account.category.category_name
            amount = txn.amount

            category_data[category]["total_spent"] += float(amount)
            category_data[category]["transactions"] += 1
            total_spending += float(amount)

        # Calculate percentages
        results = []
        for category, data in category_data.items():
            percent = (
                (data["total_spent"] / total_spending) * 100
                if total_spending > 0 else 0
            )

            results.append({
                "category": category,
                "total_spent": round(data["total_spent"], 2),
                "transactions": data["transactions"],
                "percentage": round(percent, 2)
            })

        # Sort highest spending first
        results.sort(key=lambda x: x["total_spent"], reverse=True)

        return Response({
            "total_spent": round(total_spending, 2),
            "categories": results
        })


class AccountTransactionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, account_id):
        user = request.user

        account = get_object_or_404(Account, id=account_id, user=user)

        transactions = Transaction.objects.filter(
            user=user
        ).filter(
            Q(source_account=account) | Q(destination_account=account)
        ).order_by("-created_at")

        data = [
            {
                "id": t.id,
                "type": t.transaction_type,
                "amount": t.amount,
                "direction": "OUT" if t.source_account == account else "IN",
                "source": t.source_account.account_name if t.source_account else None,
                "destination": t.destination_account.account_name if t.destination_account else None,
                "status": t.status,
                "created_at": t.created_at,
            }
            for t in transactions
        ]

        return Response({
            "account": account.account_name,
            "balance": account.balance,
            "transactions": data
        })


class AllAccountsTransactionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        accounts = Account.objects.filter(user=user)

        transactions = Transaction.objects.filter(
            user=user
        ).filter(
            Q(source_account__in=accounts) |
            Q(destination_account__in=accounts)
        ).order_by("-created_at")

        data = [
            {
                "id": t.id,
                "type": t.transaction_type,
                "amount": t.amount,
                "status": t.status,
                "source": t.source_account.account_name if t.source_account else None,
                "destination": t.destination_account.account_name if t.destination_account else None,
                "created_at": t.created_at,
                "direction": (
                    "OUT" if t.source_account and t.source_account.user == user else "IN"
                )
            }
            for t in transactions
        ]

        return Response({
            "total_transactions": transactions.count(),
            "transactions": data
        })