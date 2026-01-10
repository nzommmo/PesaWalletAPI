from django.urls import path
from payments.views import MpesaPaymentView, MpesaCallbackView

urlpatterns = [
    path("pay/", MpesaPaymentView.as_view()),
    path("mpesa-callback/", MpesaCallbackView.as_view()),
]
