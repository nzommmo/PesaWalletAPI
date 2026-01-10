from django.urls import path
from .views import NotificationListView, NotificationUpdateView, NotificationDeleteView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notifications-list"),
    path("<int:id>/", NotificationUpdateView.as_view(), name="notifications-update"),
    path("<int:id>/delete/", NotificationDeleteView.as_view(), name="notifications-delete"),
]
