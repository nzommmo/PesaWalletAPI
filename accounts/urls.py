from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import AccountViewSet, AccountTransactionsView,AllAccountsTransactionsView, ChangePasswordView

router = DefaultRouter()
router.register(r"accounts", AccountViewSet, basename="accounts")

urlpatterns = router.urls + [
    path(
        "accounts/<int:account_id>/transactions/",
        AccountTransactionsView.as_view(),
        name="account-transactions",
    ),
    path(
        "recent/transactions/",
        AllAccountsTransactionsView.as_view(),
        name="all-transactions",
    ),
    path(
        "users/change-password/",
        ChangePasswordView.as_view(),
        name="change-password"
    ),

]