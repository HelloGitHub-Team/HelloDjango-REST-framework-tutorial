from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.fields import CharField

from drf_haystack.serializers import (
    HaystackSerializer,
    HaystackSerializerMixin,
    HighlighterMixin,
)

from .models import Category, Post, Tag
from .search_indexes import PostIndex
from .utils import Highlighter


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
        ]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
        ]


class PostListSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    author = UserSerializer()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "created_time",
            "excerpt",
            "category",
            "author",
            "views",
        ]


class PostRetrieveSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    author = UserSerializer()
    tags = TagSerializer(many=True)
    toc = serializers.CharField()
    body_html = serializers.CharField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "body",
            "created_time",
            "modified_time",
            "excerpt",
            "views",
            "category",
            "author",
            "tags",
            "toc",
            "body_html",
        ]


class HighlightedCharField(CharField):
    def to_representation(self, value):
        value = super().to_representation(value)
        request = self.context["request"]
        query = request.query_params["text"]
        highlighter = Highlighter(query)
        return highlighter.highlight(value)


class PostHaystackSerializer(HaystackSerializerMixin, PostListSerializer):
    title = HighlightedCharField()
    summary = HighlightedCharField(source="body")

    class Meta(PostListSerializer.Meta):
        search_fields = ["text"]
        fields = [
            "id",
            "title",
            "summary",
            "created_time",
            "excerpt",
            "category",
            "author",
            "views",
        ]
