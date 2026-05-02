from django.urls import path
from .views import (
    AdminOverviewView,
    AdminUsersView,
    AdminTransactionsView,
    AdminUserDetailView,      # ← add
)

urlpatterns = [
    path("overview/", AdminOverviewView.as_view()),
    path("users/", AdminUsersView.as_view()),
    path("users/<int:user_id>/", AdminUserDetailView.as_view()),   # ← add
    path("transactions/", AdminTransactionsView.as_view()),
]