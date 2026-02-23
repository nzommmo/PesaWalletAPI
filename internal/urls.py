from django.urls import path
from .views import (
    AdminOverviewView,
    AdminUsersView,
    AdminTransactionsView
)

urlpatterns = [
    path("overview/", AdminOverviewView.as_view()),
    path("users/", AdminUsersView.as_view()),
    path("transactions/", AdminTransactionsView.as_view()),
]