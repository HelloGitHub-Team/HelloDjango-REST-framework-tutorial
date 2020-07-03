"""blogproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

import blog.views
import comments.views
from blog.feeds import AllPostsRssFeed

router = routers.DefaultRouter()
router.register(r"posts", blog.views.PostViewSet, basename="post")
router.register(r"categories", blog.views.CategoryViewSet, basename="category")
router.register(r"tags", blog.views.TagViewSet, basename="tag")
router.register(r"comments", comments.views.CommentViewSet, basename="comment")
router.register(r"search", blog.views.PostSearchView, basename="search")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("search/", include("haystack.urls")),
    path("", include("blog.urls")),
    path("", include("comments.urls")),
    path("api/", include(router.urls)),
    path("api/auth/", include("rest_framework.urls", namespace="rest_framework")),
    # 记得在顶部引入 AllPostsRssFeed
    path("all/rss/", AllPostsRssFeed(), name="rss"),
]
