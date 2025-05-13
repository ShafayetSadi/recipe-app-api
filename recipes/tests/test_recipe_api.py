from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipes.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse("recipes:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse("recipes:recipe-detail", args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe."""
    defaults = {
        "title": "Sample Recipe",
        "time_minutes": 10,
        "price": Decimal("5.00"),
        "description": "Sample description",
        "link": "http://example.com/recipe.pdf",
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """Create and return a sample user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test the publicly available recipe API."""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the recipe endpoint."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test the authorized user recipe API."""

    def setUp(self):
        self.user = create_user(
            email="test@example.com",
            password="testpass",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user, title="Recipe 1")
        create_recipe(user=self.user, title="Recipe 2")
        create_recipe(user=self.user, title="Another Recipe")

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test that recipes returned are for the authenticated user."""
        other_user = create_user(
            email="other@example.com",
            password="password123",
        )
        create_recipe(user=other_user, title="Recipe 1")
        create_recipe(user=self.user, title="Recipe 2")

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user).order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe."""
        payload = {
            "title": "Sample Recipe",
            "time_minutes": 10,
            "price": Decimal("5.00"),
            "description": "Sample description",
            "link": "http://example.com/recipe.pdf",
        }
        res = self.client.post(RECIPES_URL, payload)
        recipe = Recipe.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """Test updating a recipe with PATCH."""
        original_link = "http://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title="Sample Recipe",
            link=original_link,
        )
        payload = {"title": "Updated Recipe"}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """Test updating a recipe with PUT."""
        recipe = create_recipe(
            user=self.user,
            title="Sample Recipe",
            time_minutes=10,
            price=Decimal("5.00"),
            link="http://example.com/recipe.pdf",
            description="Sample description",
        )
        payload = {
            "title": "Updated Recipe",
            "time_minutes": 20,
            "price": Decimal("10.00"),
            "link": "http://example.com/updated_recipe.pdf",
            "description": "Updated description",
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recipe user results in an error."""
        new_user = create_user(
            email="newuser@example.com",
            password="newpassword123",
        )
        recipe = create_recipe(user=self.user)
        payload = {"user": new_user.id}

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        recipes = Recipe.objects.filter(id=recipe.id)
        self.assertFalse(recipes.exists())

    def test_delete_other_users_recipe_error(self):
        """Test trying to delete another user's recipe results in an error."""
        other_user = create_user(
            email="newuser@example.com",
            password="newpassword123",
        )
        recipe = create_recipe(user=other_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
