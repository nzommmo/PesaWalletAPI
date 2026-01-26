from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from decimal import Decimal
from transactions.models import Transaction
from notifications.models import Notification
from transactions.serializers import AllocateFundsSerializer,TopUpSerializer,IncomeSerializer,TransactionSerializer
from accounts.models import Account
from datetime import timedelta
from django.utils import timezone
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.conf import settings
from django.db import transaction as db_transaction
import requests  # Add this import


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
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount = serializer.validated_data['amount']
        
        # Validate user email
        if not request.user.email:
            return Response(
                {"error": "User email is required. Please update your profile."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user's primary account
        try:
            primary_account = Account.objects.get(
                user=request.user, 
                account_type='PRIMARY'
            )
        except Account.DoesNotExist:
            return Response(
                {"error": "Primary account not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # For KES, convert to cents
        amount_in_cents = int(amount * 100)

        # Paystack API endpoint
        url = "https://api.paystack.co/transaction/initialize"
        
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        # Generate unique reference
        import uuid
        unique_ref = f"topup_{request.user.id}_{uuid.uuid4().hex[:8]}"
        
        # Determine callback URL based on platform
        # Frontend can send a 'platform' field: 'web' or 'mobile'
        platform = request.data.get('platform', 'web')
        
        if platform == 'mobile':
            # Deep link for mobile app
            callback_url = f"{settings.MOBILE_APP_SCHEME}://payment/verify"
        else:
            # Web URL
            callback_url = f"{settings.FRONTEND_URL}/top-up"
        
        payload = {
            "email": request.user.email,
            "amount": amount_in_cents,
            "currency": "KES",
            "reference": unique_ref,
            "callback_url": callback_url,
            "metadata": {
                "user_id": str(request.user.id),
                "account_id": str(primary_account.id),
                "platform": platform,
                "custom_fields": [
                    {
                        "display_name": "User",
                        "variable_name": "user",
                        "value": request.user.email
                    }
                ]
            }
        }

        try:
            print(f"Initializing Paystack payment: {payload}")
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response_data = response.json()
            
            print(f"Paystack response: {response_data}")

            if response_data.get('status') == True:
                # Create pending transaction record
                txn = Transaction.objects.create(
                    user=request.user,
                    destination_account=primary_account,
                    amount=amount,
                    transaction_type='INCOME',
                    status='PENDING',
                    reference=unique_ref
                )

                return Response({
                    'authorization_url': response_data['data']['authorization_url'],
                    'access_code': response_data['data']['access_code'],
                    'reference': unique_ref,
                    'platform': platform
                }, status=status.HTTP_200_OK)
            else:
                error_message = response_data.get('message', 'Failed to initialize payment')
                print(f"Paystack error: {error_message}")
                return Response(
                    {"error": error_message}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        except requests.Timeout:
            return Response(
                {"error": "Payment gateway timeout. Please try again."}, 
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except Exception as e:
            print(f"Exception: {str(e)}")
            return Response(
                {"error": f"Payment initialization failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyTopUpView(APIView):
    permission_classes = []  # Public endpoint

    def get(self, request):
        reference = request.query_params.get('reference')
        
        print(f"\n{'='*50}")
        print(f"VERIFICATION REQUEST RECEIVED")
        print(f"Reference: {reference}")
        print(f"Query params: {request.query_params}")
        print(f"{'='*50}\n")
        
        if not reference:
            return Response(
                {"error": "Reference is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Paystack API endpoint
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        }

        try:
            print(f"Verifying transaction with Paystack: {reference}")
            
            # Verify transaction with Paystack
            response = requests.get(url, headers=headers)
            response_data = response.json()
            
            print(f"Paystack verification response: {response_data}")

            if response_data.get('status') and response_data['data']['status'] == 'success':
                # Get the transaction record
                try:
                    txn = Transaction.objects.get(reference=reference)
                    print(f"Transaction found: {txn.id}, Status: {txn.status}")
                except Transaction.DoesNotExist:
                    print(f"Transaction NOT found with reference: {reference}")
                    return Response(
                        {"error": "Transaction not found"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )

                if txn.status == 'PENDING':
                    # Update transaction and account balance atomically
                    with db_transaction.atomic():
                        txn.status = 'SUCCESS'
                        txn.save()

                        # Update account balance
                        account = txn.destination_account
                        old_balance = account.balance
                        account.balance += txn.amount
                        account.save()

                        print(f"Account updated: {old_balance} -> {account.balance}")

                        # Create success notification
                        Notification.objects.create(
                            user=txn.user,
                            notification_type="SUCCESS",
                            message=f"Account topped up with KES {txn.amount}"
                        )
                    
                    print(f"Transaction {reference} verified successfully!")

                    return Response({
                        'status': 'success',
                        'message': 'Payment verified successfully',
                        'amount': str(txn.amount),
                        'new_balance': str(account.balance)
                    }, status=status.HTTP_200_OK)
                else:
                    print(f"Transaction already processed. Current status: {txn.status}")
                    return Response({
                        'status': 'already_processed',
                        'message': 'Transaction already processed',
                        'amount': str(txn.amount),
                        'new_balance': str(txn.destination_account.balance)
                    }, status=status.HTTP_200_OK)
            else:
                print(f"Paystack verification failed: {response_data}")
                # Update transaction status to failed
                try:
                    txn = Transaction.objects.get(reference=reference)
                    if txn.status == 'PENDING':
                        txn.status = 'FAILED'
                        txn.save()
                        
                        # Create failure notification
                        Notification.objects.create(
                            user=txn.user,
                            notification_type="ERROR",
                            message=f"Top up payment failed"
                        )
                except Transaction.DoesNotExist:
                    pass

                return Response({
                    'status': 'failed',
                    'message': 'Payment verification failed'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Verification exception: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        accounts = Account.objects.filter(user=user)
        total_balance = sum(a.balance for a in accounts)

        accounts_data = [
            {
                "account_name": a.account_name,
                "balance": a.balance,
                "account_type": a.account_type
            } for a in accounts
        ]

        last_month = timezone.now() - timedelta(days=30)
        transactions = Transaction.objects.filter(
            user=user,
            created_at__gte=last_month
        ).order_by('-created_at')

        transactions_data = [
            {
                "transaction_type": t.transaction_type,
                "amount": t.amount,
                "status": t.status,
                "created_at": t.created_at
            } for t in transactions
        ]

        return Response({
            "total_balance": total_balance,
            "accounts": accounts_data,
            "transactions_last_month": transactions_data
        })
    

class IncomeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = IncomeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        account = serializer.validated_data["account"]
        amount = serializer.validated_data["amount"]

        with transaction.atomic():
            # Update account balance
            account.balance += amount
            account.save()

            # Create transaction
            txn = Transaction.objects.create(
                user=request.user,
                destination_account=account,
                amount=amount,
                transaction_type="INCOME",
                status="SUCCESS"
            )

            # Create notification
            Notification.objects.create(
                user=request.user,
                notification_type="SUCCESS",
                message=f"Income of {amount} added to {account.account_name}"
            )

        return Response(
            {
                "message": f"Income of {amount} added successfully",
                "transaction_id": txn.id,
                "account_balance": account.balance
            },
            status=status.HTTP_201_CREATED
        )
    

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

        serializer = TransactionSerializer(transactions, many=True)

        return Response({
            "account": {
                "id": account.id,
                "name": account.account_name,
                "balance": account.balance,
                "limit": account.limit_amount,
            },
            "transactions": serializer.data
        })