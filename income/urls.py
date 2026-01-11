from django.urls import path
from .views import IncomeListCreateView, IncomeDetailView,IncomeDeleteView

urlpatterns = [
    path("", IncomeListCreateView.as_view(), name="income-list-create"),  # GET all / POST create
    path("<int:id>/", IncomeDetailView.as_view(), name="income-detail"),   # GET, PUT, PATCH, DELETE
    path("<int:id>/delete/", IncomeDeleteView.as_view(), name="income-delete"),

]
