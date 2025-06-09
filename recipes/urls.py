from django.urls import path, include

from rest_framework.routers import DefaultRouter

from recipes.views import RecipeViewSet, TagViewSet

router = DefaultRouter()
router.register("recipes", RecipeViewSet)
router.register("tags", TagViewSet, basename="tag")

app_name = "recipes"
urlpatterns = [
    path("", include(router.urls)),
]
