from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from .models import Income
from .serializers import IncomeSerializer, PrimaryTopUpSerializer
from accounts.utils import get_primary_account
from transactions.models import Transaction
from notifications.models import Notification
from income.tasks import IncomeTaskManager


class IncomeListCreateView(generics.ListCreateAPIView):
    """
    GET: List all incomes for authenticated user
    POST: Create a new income
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = IncomeSerializer

    def get_queryset(self):
        IncomeTaskManager.process_user_incomes(self.request.user)
        return Income.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IncomeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single income
    PUT: Full update of an income
    PATCH: Partial update of an income
    DELETE: Delete an income
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = IncomeSerializer
    lookup_field = "pk"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return Income.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """Override to add debugging"""
        print(f"GET request - kwargs: {kwargs}, user: {request.user}")
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Override to add debugging"""
        print(f"PUT/PATCH request - kwargs: {kwargs}, user: {request.user}")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Override to add debugging"""
        print(f"DELETE request - kwargs: {kwargs}, user: {request.user}")
        return super().destroy(request, *args, **kwargs)


class IncomeDeleteView(generics.DestroyAPIView):
    """
    DELETE: Delete an income (alternative endpoint)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = IncomeSerializer
    lookup_field = "pk"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return Income.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Override to add debugging"""
        print(f"DELETE request - kwargs: {kwargs}, user: {request.user}")
        return super().destroy(request, *args, **kwargs)


class PrimaryTopUpView(APIView):
    """
    POST: Top up the primary account
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PrimaryTopUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        description = serializer.validated_data["description"]
        user = request.user

        with transaction.atomic():
            primary = get_primary_account(user)
            primary.balance += amount
            primary.save()

            Transaction.objects.create(
                user=user,
                destination_account=primary,
                amount=amount,
                transaction_type="INCOME",
                status="SUCCESS",
            )

            Notification.objects.create(
                user=user,
                notification_type="SUCCESS",
                message=f"Primary account topped up: {amount} ({description})",
            )

        return Response(
            {
                "message": "Primary account topped up successfully",
                "amount": str(amount),
                "new_balance": str(primary.balance)
            },
            status=status.HTTP_200_OK,
        )