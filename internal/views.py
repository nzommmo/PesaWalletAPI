from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from django.contrib.auth.hashers import make_password

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
            "payment_breakdown": payments,
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
                "total_balance": total_balance,
                "is_active": user.is_active,
            })

        return Response(data)

    def post(self, request):
        """Create a new user."""
        email = request.data.get("email")
        phone = request.data.get("phone")
        password = request.data.get("password")
        is_active = request.data.get("is_active", True)
        is_staff = request.data.get("is_staff", False)

        # Validate required fields
        errors = {}
        if not email:
            errors["email"] = "Email is required."
        if not phone:
            errors["phone"] = "Phone number is required."
        if not password:
            errors["password"] = "Password is required."
        if errors:
            return Response(errors, status=400)

        # Check uniqueness
        if User.objects.filter(email=email).exists():
            return Response({"email": "A user with this email already exists."}, status=400)
        if User.objects.filter(phone_number=phone).exists():
            return Response({"phone": "A user with this phone number already exists."}, status=400)

        user = User.objects.create(
            email=email,
            phone_number=phone,
            password=make_password(password),
            is_active=is_active,
            is_staff=is_staff,
        )

        return Response({
            "user_id": user.id,
            "email": user.email,
            "phone": user.phone_number,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
        }, status=201)


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
                "created_at": t.created_at,
            }
            for t in transactions[:200]
        ]

        return Response(data)


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminUser]

    def _get_user(self, user_id):
        try:
            return User.objects.get(id=user_id), None
        except User.DoesNotExist:
            return None, Response({"error": "User not found."}, status=404)

    def get(self, request, user_id):
        """Retrieve full details for a single user."""
        user, err = self._get_user(user_id)
        if err:
            return err

        accounts = Account.objects.filter(user=user)
        total_balance = sum(a.balance for a in accounts)

        return Response({
            "user_id": user.id,
            "email": user.email,
            "phone": user.phone_number,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "date_joined": user.date_joined,
            "accounts_count": accounts.count(),
            "total_balance": total_balance,
        })

    def patch(self, request, user_id):
        """Partially update a user (e.g. toggle is_active, update email/phone)."""
        user, err = self._get_user(user_id)
        if err:
            return err

        # is_active toggle — keep existing guard
        if "is_active" in request.data:
            if user == request.user:
                return Response(
                    {"error": "You cannot deactivate your own account."}, status=400
                )
            user.is_active = request.data["is_active"]

        if "email" in request.data:
            new_email = request.data["email"]
            if User.objects.filter(email=new_email).exclude(id=user_id).exists():
                return Response({"email": "This email is already in use."}, status=400)
            user.email = new_email

        if "phone" in request.data:
            new_phone = request.data["phone"]
            if User.objects.filter(phone_number=new_phone).exclude(id=user_id).exists():
                return Response({"phone": "This phone number is already in use."}, status=400)
            user.phone_number = new_phone

        if "is_staff" in request.data:
            user.is_staff = request.data["is_staff"]

        if "password" in request.data:
            user.password = make_password(request.data["password"])

        user.save()

        return Response({
            "user_id": user.id,
            "email": user.email,
            "phone": user.phone_number,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
        })

    def put(self, request, user_id):
        """Fully replace a user's editable details."""
        user, err = self._get_user(user_id)
        if err:
            return err

        email = request.data.get("email")
        phone = request.data.get("phone")

        errors = {}
        if not email:
            errors["email"] = "Email is required."
        if not phone:
            errors["phone"] = "Phone number is required."
        if errors:
            return Response(errors, status=400)

        if User.objects.filter(email=email).exclude(id=user_id).exists():
            return Response({"email": "This email is already in use."}, status=400)
        if User.objects.filter(phone_number=phone).exclude(id=user_id).exists():
            return Response({"phone": "This phone number is already in use."}, status=400)

        user.email = email
        user.phone_number = phone
        user.is_active = request.data.get("is_active", user.is_active)
        user.is_staff = request.data.get("is_staff", user.is_staff)

        if "password" in request.data:
            user.password = make_password(request.data["password"])

        user.save()

        return Response({
            "user_id": user.id,
            "email": user.email,
            "phone": user.phone_number,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
        })

    def delete(self, request, user_id):
        """Permanently delete a user and all associated data."""
        user, err = self._get_user(user_id)
        if err:
            return err

        if user == request.user:
            return Response(
                {"error": "You cannot delete your own account."}, status=400
            )

        user.delete()
        return Response({"detail": f"User {user_id} deleted successfully."}, status=200)