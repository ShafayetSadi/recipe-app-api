from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipes.serializers import IngredientSerializer

INGREDIENTS_URL = reverse("recipes:ingredient-list")


def details_url(ingredient_id):
    """Create and return a URL for the ingredient detail."""
    return reverse("recipes:ingredient-detail", args=[ingredient_id])


def create_user(email="user@example.com", password="testpassword"):
    return get_user_model().objects.create_user(email=email, password=password)  # type: ignore


class PublicIngredientApiTests(TestCase):
    """Test the publicly available ingredient API."""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the ingredients API."""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test the private ingredients API."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients."""
        Ingredient.objects.create(user=self.user, name="Ingredient 1")
        Ingredient.objects.create(user=self.user, name="Ingredient 2")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore

    def test_ingredients_limited_to_user(self):
        """Test that ingredients returned are for the authenticated user."""
        Ingredient.objects.create(user=self.user, name="Ingredient 1")
        other_user = create_user(email="other@example.com")
        Ingredient.objects.create(user=other_user, name="Ingredient 2")
        Ingredient.objects.create(user=other_user, name="Ingredient 3")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.filter(user=self.user).order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)  # type: ignore
        self.assertEqual(res.data[0]["name"], "Ingredient 1")  # type: ignore
        self.assertEqual(res.data, serializer.data)  # type: ignore

    def test_create_ingredient(self):
        """Test creating a new ingredient."""
        payload = {"name": "Ingredient 1"}
        res = self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload["name"],
        ).exists()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(exists)
        self.assertEqual(Ingredient.objects.count(), 1)
        self.assertEqual(Ingredient.objects.first().name, "Ingredient 1")  # type: ignore
        self.assertEqual(Ingredient.objects.first().user, self.user)  # type: ignore

    def test_update_ingredient(self):
        """Test updating an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name="Ingredient 1")

        payload = {"name": "Updated Ingredient"}
        url = details_url(ingredient.id)  # type: ignore
        res = self.client.patch(url, payload)

        ingredient.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.name, "Updated Ingredient")
        self.assertEqual(ingredient.user, self.user)

    def test_delete_ingredient(self):
        """Test deleting an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name="Ingredient 1")

        url = details_url(ingredient.id)  # type: ignore
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())  # type: ignore

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test filtering ingredients by those assigned to recipes."""
        ingredient1 = Ingredient.objects.create(user=self.user, name="Ingredient 1")
        ingredient2 = Ingredient.objects.create(user=self.user, name="Ingredient 2")
        recipe = Recipe.objects.create(
            title="Recipe 1",
            time_minutes=10,
            price=5.00,
            user=self.user,
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)  # type: ignore
        self.assertNotIn(serializer2.data, res.data)  # type: ignore

    def test_filtered_ingredients_unique(self):
        """Test that filtered ingredients returns unique items."""
        ingredient1 = Ingredient.objects.create(user=self.user, name="Ingredient 1")
        _ = Ingredient.objects.create(user=self.user, name="Ingredient 2")
        recipe1 = Recipe.objects.create(
            title="Recipe 1",
            time_minutes=10,
            price=5.00,
            user=self.user,
        )
        recipe1.ingredients.add(ingredient1)
        recipe2 = Recipe.objects.create(
            title="Recipe 2",
            time_minutes=20,
            price=10.00,
            user=self.user,
        )
        recipe2.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)  # type: ignore
        self.assertEqual(res.data[0]["name"], "Ingredient 1")  # type: ignore
        self.assertEqual(res.data[0]["user"], self.user.id)  # type: ignore
        self.assertEqual(Ingredient.objects.count(), 2)
        self.assertEqual(Recipe.objects.count(), 2)
        self.assertEqual(ingredient1.user, self.user)
