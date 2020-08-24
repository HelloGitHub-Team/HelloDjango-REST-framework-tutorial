from datetime import datetime

from django.apps import apps
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from django.utils.timezone import utc
from rest_framework import status
from rest_framework.test import APITestCase

from blog.models import Category, Post, Tag
from blog.serializers import (
    CategorySerializer,
    PostListSerializer,
    PostRetrieveSerializer,
    TagSerializer,
)
from comments.models import Comment
from comments.serializers import CommentSerializer


class PostViewSetTestCase(APITestCase):
    def setUp(self):
        # 断开 haystack 的 signal，测试生成的文章无需生成索引
        apps.get_app_config("haystack").signal_processor.teardown()
        # 清除缓存，防止限流
        cache.clear()

        # 设置博客数据
        # post3 category2 tag2 2020-08-01 comment2 comment1
        # post2 category1 tag1 2020-07-31
        # post1 category1 tag1 2020-07-10
        user = User.objects.create_superuser(
            username="admin", email="admin@hellogithub.com", password="admin"
        )
        self.cate1 = Category.objects.create(name="category 1")
        self.cate2 = Category.objects.create(name="category 2")
        self.tag1 = Tag.objects.create(name="tag1")
        self.tag2 = Tag.objects.create(name="tag2")

        self.post1 = Post.objects.create(
            title="title 1",
            body="post 1",
            category=self.cate1,
            author=user,
            created_time=datetime(year=2020, month=7, day=10).replace(tzinfo=utc),
        )
        self.post1.tags.add(self.tag1)

        self.post2 = Post.objects.create(
            title="title 2",
            body="post 2",
            category=self.cate1,
            author=user,
            created_time=datetime(year=2020, month=7, day=31).replace(tzinfo=utc),
        )
        self.post2.tags.add(self.tag1)

        self.post3 = Post.objects.create(
            title="title 3",
            body="post 3",
            category=self.cate2,
            author=user,
            created_time=datetime(year=2020, month=8, day=1).replace(tzinfo=utc),
        )
        self.post3.tags.add(self.tag2)
        self.comment1 = Comment.objects.create(
            name="u1",
            email="u1@google.com",
            text="comment 1",
            post=self.post3,
            created_time=datetime(year=2020, month=8, day=2).replace(tzinfo=utc),
        )
        self.comment2 = Comment.objects.create(
            name="u2",
            email="u1@apple.com",
            text="comment 2",
            post=self.post3,
            created_time=datetime(year=2020, month=8, day=3).replace(tzinfo=utc),
        )

    def test_list_post(self):
        url = reverse("v1:post-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = PostListSerializer(
            instance=[self.post3, self.post2, self.post1], many=True
        )
        self.assertEqual(response.data["results"], serializer.data)

    def test_list_post_filter_by_category(self):
        url = reverse("v1:post-list")
        response = self.client.get(url, {"category": self.cate1.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = PostListSerializer(instance=[self.post2, self.post1], many=True)
        self.assertEqual(response.data["results"], serializer.data)

    def test_list_post_filter_by_tag(self):
        url = reverse("v1:post-list")
        response = self.client.get(url, {"tags": self.tag1.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = PostListSerializer(instance=[self.post2, self.post1], many=True)
        self.assertEqual(response.data["results"], serializer.data)

    def test_list_post_filter_by_archive_date(self):
        url = reverse("v1:post-list")
        response = self.client.get(url, {"created_year": 2020, "created_month": 7})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = PostListSerializer(instance=[self.post2, self.post1], many=True)
        self.assertEqual(response.data["results"], serializer.data)

    def test_retrieve_post(self):
        url = reverse("v1:post-detail", kwargs={"pk": self.post1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = PostRetrieveSerializer(instance=self.post1)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_nonexistent_post(self):
        url = reverse("v1:post-detail", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_archive_dates(self):
        url = reverse("v1:post-archive-date")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, ["2020-08", "2020-07"])

    def test_list_comments(self):
        url = reverse("v1:post-comment", kwargs={"pk": self.post3.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = CommentSerializer([self.comment2, self.comment1], many=True)
        self.assertEqual(response.data["results"], serializer.data)

    def test_list_nonexistent_post_comments(self):
        url = reverse("v1:post-comment", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CategoryViewSetTestCase(APITestCase):
    def setUp(self) -> None:
        self.cate1 = Category.objects.create(name="category 1")
        self.cate2 = Category.objects.create(name="category 2")

    def test_list_categories(self):
        url = reverse("v1:category-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = CategorySerializer([self.cate1, self.cate2], many=True)
        self.assertEqual(response.data, serializer.data)


class TagViewSetTestCase(APITestCase):
    def setUp(self) -> None:
        self.tag1 = Tag.objects.create(name="tag1")
        self.tag2 = Tag.objects.create(name="tag2")

    def test_list_tags(self):
        url = reverse("v1:tag-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = CategorySerializer([self.tag1, self.tag2], many=True)
        self.assertEqual(response.data, serializer.data)
