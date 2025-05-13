from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from core.models import Recipe
from recipes.serializers import RecipeSerializer, RecipeDetailSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """View for managing recipes in the database."""

    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore
        """Retrieve the recipes for the authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self):  # type: ignore
        """Return the appropriate serializer class based on the action."""
        if self.action == "list":
            return RecipeSerializer

        return self.serializer_class

    def perform_create(self, serializer):  # type: ignore
        """Create a new recipe."""
        serializer.save(user=self.request.user)
