from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipes.serializers import TagSerializer

TAGS_URL = reverse("recipes:tag-list")


def detail_url(tag_id):
    """Create and return a tag detail URL."""
    return reverse("recipes:tag-detail", args=[tag_id])


def create_user(email="user@example.com", password="testpass"):
    """Create a new user."""
    return get_user_model().objects.create_user(email=email, password=password)  # type: ignore


class PublicTagsApiTests(TestCase):
    """Test the publicly available tags API."""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the tags API."""
        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test the authorized user tags API."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        self.tag = Tag.objects.create(name="Test Tag", user=self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags."""
        Tag.objects.create(name="Another Tag", user=self.user)

        response = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)  # type: ignore

    def test_tags_limited_to_user(self):
        """Test that tags returned are for the authenticated user."""
        other_user = create_user(email="other@example.com")
        Tag.objects.create(name="Another Tag", user=self.user)
        Tag.objects.create(name="Other Tag", user=other_user)

        response = self.client.get(TAGS_URL)

        tags = Tag.objects.filter(user=self.user).order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)  # type: ignore
        self.assertEqual(len(response.data), 2)  # type: ignore

    def test_update_tag(self):
        """Test updating a tag."""
        payload = {"name": "Updated Tag"}
        url = detail_url(self.tag.id)  # type: ignore

        response = self.client.patch(url, payload)

        self.tag.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.tag.name, payload["name"])

    def test_delete_tag(self):
        """Test deleting a tag."""
        url = detail_url(self.tag.id)  # type: ignore
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=self.tag.id).exists())  # type: ignore

    def test_create_tag(self):
        """Test creating a new tag."""
        payload = {"name": "New Tag"}
        response = self.client.post(TAGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        tag = Tag.objects.get(id=response.data["id"])  # type: ignore
        self.assertEqual(tag.name, payload["name"])
        self.assertEqual(tag.user, self.user)
