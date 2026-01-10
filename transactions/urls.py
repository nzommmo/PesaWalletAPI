from django.urls import path
from transactions.views import (AllocateFundsView, 
TopUpView, ReportsView,IncomeView
)

urlpatterns = [
    path("allocate/", AllocateFundsView.as_view()),
    path("top-up/", TopUpView.as_view()),
    path("reports/", ReportsView.as_view()), 
    path("income/", IncomeView.as_view()), 
]
