from django.urls import path
from .views import TransferFundsView

urlpatterns = [
    path("transfer/", TransferFundsView.as_view(), name="transfer-funds"),
]
