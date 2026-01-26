from django.urls import path
from transactions.views import (
    AllocateFundsView, 
    TopUpView, 
    VerifyTopUpView,  # Add this
    ReportsView,
    IncomeView,
    AccountTransactionsView
)

urlpatterns = [
    path("allocate/", AllocateFundsView.as_view()),
    path("top-up/", TopUpView.as_view()),
    path("top-up/verify/", VerifyTopUpView.as_view()),  # Add this
    path("reports/", ReportsView.as_view()), 
    path("income/", IncomeView.as_view()),
    path("accounts/<int:account_id>/transactions/", AccountTransactionsView.as_view(), name="account-transactions"),
]