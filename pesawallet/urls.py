from django.urls import path, include

urlpatterns = [
    path("api/", include("users.urls")),
    path("api/", include("accounts.urls")),
    path("api/", include("categories.urls")),
    path("api/", include("transactions.urls")),
    path("api/", include("payments.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/", include("transactions.urls")),
    path("api/incomes/", include("income.urls")),
     path("api/payments/", include("payments.urls")), 


]
