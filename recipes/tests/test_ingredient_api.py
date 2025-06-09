from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
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
