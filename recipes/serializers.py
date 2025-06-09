from rest_framework import serializers

from core.models import Recipe, Tag, Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient objects."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "user")
        read_only_fields = ("id", "user")

    def create(self, validated_data):
        """Create an ingredient."""
        return Ingredient.objects.create(**validated_data)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects."""

    class Meta:
        model = Tag
        fields = ("id", "name", "user")
        read_only_fields = ("id", "user")


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe objects."""

    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ("id", "title", "time_minutes", "price", "link", "tags", "ingredients")
        read_only_fields = ("id",)

    def create(self, validated_data):
        """Create a recipe."""
        tags_data = validated_data.pop("tags", [])
        ingredients_data = validated_data.pop("ingredients", [])
        recipe = Recipe.objects.create(**validated_data)

        for ingredient_data in ingredients_data:
            ingredient, created = Ingredient.objects.get_or_create(
                user=self.context["request"].user,
                **ingredient_data,
            )
            recipe.ingredients.add(ingredient)

        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                user=self.context["request"].user,
                **tag_data,
            )
            recipe.tags.add(tag)

        return recipe

    def update(self, instance, validated_data):
        """Update a recipe."""
        tags_data = validated_data.pop("tags", None)
        ingredients_data = validated_data.pop("ingredients", None)
        if ingredients_data is not None:
            instance.ingredients.clear()
            for ingredient_data in ingredients_data:
                ingredient, created = Ingredient.objects.get_or_create(
                    user=self.context["request"].user,
                    **ingredient_data,
                )
                instance.ingredients.add(ingredient)
        if tags_data is not None:
            instance.tags.clear()
            for tag_data in tags_data:
                tag, created = Tag.objects.get_or_create(
                    user=self.context["request"].user,
                    **tag_data,
                )
                instance.tags.add(tag)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail objects."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ("description",)
