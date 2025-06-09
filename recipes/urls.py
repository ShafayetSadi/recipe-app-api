from django.urls import path, include

from rest_framework.routers import DefaultRouter

from recipes.views import RecipeViewSet, TagViewSet, IngredientViewSet

router = DefaultRouter()
router.register("recipes", RecipeViewSet, basename="recipe")
router.register("tags", TagViewSet, basename="tag")
router.register("ingredients", IngredientViewSet, basename="ingredient")


app_name = "recipes"
urlpatterns = [
    path("", include(router.urls)),
]
