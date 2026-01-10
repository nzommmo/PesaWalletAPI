from django.urls import path
from transactions.views import AllocateFundsView, TopUpView

urlpatterns = [
    path("allocate/", AllocateFundsView.as_view(), name="allocate-funds"),
     path("top-up/", TopUpView.as_view()),
]
