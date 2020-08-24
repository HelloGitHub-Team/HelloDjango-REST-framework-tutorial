from django.apps import apps
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from blog.models import Category, Post
from comments.models import Comment


class CommentViewSetTestCase(APITestCase):
    def setUp(self):
        self.url = reverse("v1:comment-list")
        # 断开 haystack 的 signal，测试生成的文章无需生成索引
        apps.get_app_config("haystack").signal_processor.teardown()
        user = User.objects.create_superuser(
            username="admin", email="admin@hellogithub.com", password="admin"
        )
        cate = Category.objects.create(name="测试")
        self.post = Post.objects.create(
            title="测试标题", body="测试内容", category=cate, author=user,
        )

    def test_create_valid_comment(self):
        data = {
            "name": "user",
            "email": "user@example.com",
            "text": "test comment text",
            "post": self.post.pk,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comment = Comment.objects.first()
        self.assertEqual(comment.name, data["name"])
        self.assertEqual(comment.email, data["email"])
        self.assertEqual(comment.text, data["text"])
        self.assertEqual(comment.post, self.post)

    def test_create_invalid_comment(self):
        invalid_data = {
            "name": "user",
            "email": "user@example.com",
            "text": "test comment text",
            "post": 999,
        }
        response = self.client.post(self.url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Comment.objects.count(), 0)
