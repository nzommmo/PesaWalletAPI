from rest_framework.routers import DefaultRouter
from accounts.views import AccountViewSet

router = DefaultRouter()
router.register(r"accounts", AccountViewSet, basename="accounts")

urlpatterns = router.urls
