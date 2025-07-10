from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes

from core.models import Recipe, Tag, Ingredient
from recipes.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeImageSerializer,
)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "tags",
                OpenApiTypes.STR,
                description="Comma-separated list of tag IDs to filter recipes.",
            ),
            OpenApiParameter(
                "ingredients",
                OpenApiTypes.STR,
                description="Comma-separated list of ingredient IDs to filter recipes.",
            ),
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for managing recipes in the database."""

    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):  # type: ignore
        """Retrieve the recipes for the authenticated user."""
        tags = self.request.query_params.get("tags")  # type: ignore
        ingredients = self.request.query_params.get("ingredients")  # type: ignore
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        return queryset.filter(user=self.request.user).order_by("-id").distinct()

    def get_serializer_class(self):  # type: ignore
        """Return the appropriate serializer class based on the action."""
        if self.action == "list":
            return RecipeSerializer
        elif self.action == "upload_image":
            return RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):  # type: ignore
        """Create a new recipe."""
        serializer.save(user=self.request.user)

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):  # type: ignore
        """Upload an image for a recipe."""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "assigned_only",
                OpenApiTypes.INT,
                enum=[0, 1],
                description="Filter attributes that are assigned to recipes.",
            )
        ],
    )
)
class BaseRecipeAttrViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Base viewset for recipe attributes."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve the attributes for the authenticated user."""
        assigned_only = bool(int(self.request.query_params.get("assigned_only", 0)))  # type: ignore
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipes__isnull=False)  # type: ignore
        return queryset.filter(user=self.request.user).order_by("-name").distinct()  # type: ignore

    def perform_create(self, serializer):
        """Create a new attribute."""
        serializer.save(user=self.request.user)
        return serializer.data


class TagViewSet(BaseRecipeAttrViewSet):
    """View for managing tags in the database."""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """View for managing ingredients in the database."""

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
