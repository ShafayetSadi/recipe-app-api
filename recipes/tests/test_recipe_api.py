from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

import tempfile
import os
from PIL import Image

from core.models import Recipe, Tag, Ingredient
from recipes.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse("recipes:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse("recipes:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """Create and return a recipe image upload URL."""
    return reverse("recipes:recipe-upload-image", args=[recipe_id])


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
        self.assertEqual(res.data, serializer.data)  # type: ignore

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
        self.assertEqual(res.data, serializer.data)  # type: ignore

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)  # type: ignore
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore

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
        recipe = Recipe.objects.get(id=res.data["id"])  # type: ignore

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

        url = detail_url(recipe.id)  # type: ignore
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

        url = detail_url(recipe.id)  # type: ignore
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
        payload = {"user": new_user.id}  # type: ignore

        url = detail_url(recipe.id)  # type: ignore
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)  # type: ignore
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        recipes = Recipe.objects.filter(id=recipe.id)  # type: ignore
        self.assertFalse(recipes.exists())

    def test_delete_other_users_recipe_error(self):
        """Test trying to delete another user's recipe results in an error."""
        other_user = create_user(
            email="newuser@example.com",
            password="newpassword123",
        )
        recipe = create_recipe(user=other_user)

        url = detail_url(recipe.id)  # type: ignore
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())  # type: ignore

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""
        payload = {
            "title": "Recipe with Tags",
            "time_minutes": 15,
            "price": Decimal("7.50"),
            "description": "Recipe description",
            "link": "http://example.com/recipe_with_tags.pdf",
            "tags": [{"name": "Tag1"}, {"name": "Tag2"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])  # type: ignore
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            self.assertTrue(
                recipe.tags.filter(name=tag["name"], user=self.user).exists()
            )

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags."""
        tag1 = Tag.objects.create(user=self.user, name="Tag1")
        tag2 = Tag.objects.create(user=self.user, name="Tag2")
        payload = {
            "title": "Recipe with Existing Tags",
            "time_minutes": 20,
            "price": Decimal("8.00"),
            "description": "Recipe description",
            "link": "http://example.com/recipe_with_existing_tags.pdf",
            "tags": [{"name": tag1.name}, {"name": tag2.name}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])  # type: ignore
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag1, recipe.tags.all())
        self.assertIn(tag2, recipe.tags.all())
        for tag in payload["tags"]:
            self.assertTrue(
                recipe.tags.filter(name=tag["name"], user=self.user).exists()
            )

    def test_create_tag_on_update(self):
        """Test creating a tag when updating a recipe."""
        recipe = create_recipe(user=self.user, title="Recipe to Update")
        payload = {
            "title": "Updated Recipe",
            "tags": [{"name": "New Tag"}],
        }

        url = detail_url(recipe.id)  # type: ignore
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(name="New Tag", user=self.user)
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assigns_tags(self):
        """Test updating a recipe assigns existing tags."""
        tag1 = Tag.objects.create(user=self.user, name="Tag1")
        tag2 = Tag.objects.create(user=self.user, name="Tag2")
        recipe = create_recipe(user=self.user, title="Recipe to Update")
        recipe.tags.add(tag1)

        payload = {
            "title": "Updated Recipe",
            "tags": [{"name": tag2.name}],
        }

        url = detail_url(recipe.id)  # type: ignore
        res = self.client.patch(url, payload, format="json")

        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 1)
        self.assertIn(tag2, recipe.tags.all())
        self.assertNotIn(tag1, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing a recipe's tags."""
        tag1 = Tag.objects.create(user=self.user, name="Tag1")
        tag2 = Tag.objects.create(user=self.user, name="Tag2")
        recipe = create_recipe(user=self.user, title="Recipe to Clear Tags")
        recipe.tags.add(tag1, tag2)

        payload = {"tags": []}

        url = detail_url(recipe.id)  # type: ignore
        res = self.client.patch(url, payload, format="json")

        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
        self.assertNotIn(tag1, recipe.tags.all())
        self.assertNotIn(tag2, recipe.tags.all())

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients."""
        payload = {
            "title": "Recipe with Ingredients",
            "time_minutes": 15,
            "price": Decimal("7.50"),
            "description": "Recipe description",
            "ingredients": [{"name": "Ingredient1"}, {"name": "Ingredient2"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        recipe = Recipe.objects.get(id=res.data["id"])  # type: ignore

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            self.assertTrue(
                recipe.ingredients.filter(
                    name=ingredient["name"], user=self.user
                ).exists()
            )

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating a recipe with existing ingredients."""
        ingredient1 = Ingredient.objects.create(user=self.user, name="Ingredient1")
        ingredient2 = Ingredient.objects.create(user=self.user, name="Ingredient2")
        payload = {
            "title": "Recipe with Existing Ingredients",
            "time_minutes": 20,
            "price": Decimal("8.00"),
            "description": "Recipe description",
            "ingredients": [{"name": ingredient1.name}, {"name": ingredient2.name}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        recipe = Recipe.objects.get(id=res.data["id"])  # type: ignore

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient1, recipe.ingredients.all())
        self.assertIn(ingredient2, recipe.ingredients.all())
        for ingredient in payload["ingredients"]:
            self.assertTrue(
                recipe.ingredients.filter(
                    name=ingredient["name"], user=self.user
                ).exists()
            )

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when updating a recipe."""
        recipe = create_recipe(user=self.user, title="Recipe to Update")
        payload = {
            "title": "Updated Recipe",
            "ingredients": [{"name": "New Ingredient"}],
        }

        url = detail_url(recipe.id)  # type: ignore
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        new_ingredient = Ingredient.objects.get(name="New Ingredient", user=self.user)
        self.assertIn(new_ingredient, recipe.ingredients.all())
        self.assertEqual(recipe.ingredients.count(), 1)

    def test_update_recipe_assigns_ingredients(self):
        """Test updating a recipe assigns existing ingredients."""
        ingredient1 = Ingredient.objects.create(user=self.user, name="Ingredient1")
        ingredient2 = Ingredient.objects.create(user=self.user, name="Ingredient2")
        recipe = create_recipe(user=self.user, title="Recipe to Update")
        recipe.ingredients.add(ingredient1)

        payload = {
            "title": "Updated Recipe",
            "ingredients": [{"name": ingredient2.name}],
        }

        url = detail_url(recipe.id)  # type: ignore
        res = self.client.patch(url, payload, format="json")

        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing a recipe's ingredients."""
        ingredient1 = Ingredient.objects.create(user=self.user, name="Ingredient1")
        ingredient2 = Ingredient.objects.create(user=self.user, name="Ingredient2")
        recipe = create_recipe(user=self.user, title="Recipe to Clear Ingredients")
        recipe.ingredients.add(ingredient1, ingredient2)

        payload = {"ingredients": []}

        url = detail_url(recipe.id)  # type: ignore
        res = self.client.patch(url, payload, format="json")

        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
        self.assertNotIn(ingredient1, recipe.ingredients.all())
        self.assertNotIn(ingredient2, recipe.ingredients.all())

    def test_filter_recipes_by_tags(self):
        """Test filtering recipes by tags."""
        recipe1 = create_recipe(user=self.user, title="Recipe 1")
        recipe2 = create_recipe(user=self.user, title="Recipe 2")
        tag1 = Tag.objects.create(user=self.user, name="Tag1")
        tag2 = Tag.objects.create(user=self.user, name="Tag2")
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        _recipe3 = create_recipe(user=self.user, title="Recipe 3")

        res = self.client.get(RECIPES_URL, {"tags": f"{tag1.id},{tag2.id}"})  # type: ignore

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)  # type: ignore

        s1 = RecipeSerializer(recipe1)
        s2 = RecipeSerializer(recipe2)
        s3 = RecipeSerializer(_recipe3)
        self.assertIn(s1.data, res.data)  # type: ignore
        self.assertIn(s2.data, res.data)  # type: ignore
        self.assertNotIn(s3.data, res.data)  # type: ignore

    def test_filter_recipes_by_ingredients(self):
        """Test filtering recipes by ingredients."""
        recipe1 = create_recipe(user=self.user, title="Recipe 1")
        recipe2 = create_recipe(user=self.user, title="Recipe 2")
        ingredient1 = Ingredient.objects.create(user=self.user, name="Ingredient1")
        ingredient2 = Ingredient.objects.create(user=self.user, name="Ingredient2")
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        _recipe3 = create_recipe(user=self.user, title="Recipe 3")

        res = self.client.get(
            RECIPES_URL,
            {"ingredients": f"{ingredient1.id},{ingredient2.id}"},  # type: ignore
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)  # type: ignore

        s1 = RecipeSerializer(recipe1)
        s2 = RecipeSerializer(recipe2)
        s3 = RecipeSerializer(_recipe3)
        self.assertIn(s1.data, res.data)  # type: ignore
        self.assertIn(s2.data, res.data)  # type: ignore
        self.assertNotIn(s3.data, res.data)  # type: ignore


class ImageUploadTests(TestCase):
    """Test image upload functionality for recipes."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="user@example.com",
            password="testpass",
        )
        self.client.force_authenticate(user=self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        """Clean up any temporary files created during tests."""
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading an image to a recipe."""
        url = image_upload_url(self.recipe.id)  # type: ignore
        with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
            image = Image.new("RGB", (100, 100))
            image.save(temp_file, format="JPEG")
            temp_file.seek(0)

            res = self.client.post(
                url,
                {"image": temp_file},
                format="multipart",
            )

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)  # type: ignore
        self.assertTrue(os.path.exists(self.recipe.image.path))
        self.assertTrue(res.data["image"].endswith(self.recipe.image.url))  # type: ignore

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image fails."""
        url = image_upload_url(self.recipe.id)  # type: ignore

        res = self.client.post(
            url,
            {"image": "notanimage"},
            format="multipart",
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
