from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from categories.models import Category
from categories.serializers import CategorySerializer

class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
