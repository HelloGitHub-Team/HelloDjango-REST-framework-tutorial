from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView
from django_filters.rest_framework import DjangoFilterBackend
from drf_haystack.viewsets import HaystackViewSet
from drf_yasg import openapi
from drf_yasg.inspectors import FilterInspector
from drf_yasg.utils import swagger_auto_schema
from pure_pagination.mixins import PaginationMixin
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import DateField
from rest_framework.throttling import AnonRateThrottle
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.key_constructor.bits import ListSqlQueryKeyBit, PaginationKeyBit, RetrieveSqlQueryKeyBit
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor

from comments.serializers import CommentSerializer

from .filters import PostFilter
from .models import Category, Post, Tag
from .serializers import (
    CategorySerializer, PostHaystackSerializer, PostListSerializer, PostRetrieveSerializer, TagSerializer)
from .utils import UpdatedAtKeyBit


class IndexView(PaginationMixin, ListView):
    model = Post
    template_name = "blog/index.html"
    context_object_name = "post_list"
    paginate_by = 10


class CategoryView(IndexView):
    def get_queryset(self):
        cate = get_object_or_404(Category, pk=self.kwargs.get("pk"))
        return super().get_queryset().filter(category=cate)


class ArchiveView(IndexView):
    def get_queryset(self):
        year = self.kwargs.get("year")
        month = self.kwargs.get("month")
        return (
            super()
            .get_queryset()
            .filter(created_time__year=year, created_time__month=month)
        )


class TagView(IndexView):
    def get_queryset(self):
        t = get_object_or_404(Tag, pk=self.kwargs.get("pk"))
        return super().get_queryset().filter(tags=t)


# 记得在顶部导入 DetailView
class PostDetailView(DetailView):
    # 这些属性的含义和 ListView 是一样的
    model = Post
    template_name = "blog/detail.html"
    context_object_name = "post"

    def get(self, request, *args, **kwargs):
        # 覆写 get 方法的目的是因为每当文章被访问一次，就得将文章阅读量 +1
        # get 方法返回的是一个 HttpResponse 实例
        # 之所以需要先调用父类的 get 方法，是因为只有当 get 方法被调用后，
        # 才有 self.object 属性，其值为 Post 模型实例，即被访问的文章 post
        response = super().get(request, *args, **kwargs)

        # 将文章阅读量 +1
        # 注意 self.object 的值就是被访问的文章 post
        self.object.increase_views()

        # 视图必须返回一个 HttpResponse 对象
        return response


# ---------------------------------------------------------------------------
#   Django REST framework 接口
# ---------------------------------------------------------------------------


class PostUpdatedAtKeyBit(UpdatedAtKeyBit):
    key = "post_updated_at"


class CommentUpdatedAtKeyBit(UpdatedAtKeyBit):
    key = "comment_updated_at"


class PostListKeyConstructor(DefaultKeyConstructor):
    list_sql = ListSqlQueryKeyBit()
    pagination = PaginationKeyBit()
    updated_at = PostUpdatedAtKeyBit()


class PostObjectKeyConstructor(DefaultKeyConstructor):
    retrieve_sql = RetrieveSqlQueryKeyBit()
    updated_at = PostUpdatedAtKeyBit()


class CommentListKeyConstructor(DefaultKeyConstructor):
    list_sql = ListSqlQueryKeyBit()
    pagination = PaginationKeyBit()
    updated_at = CommentUpdatedAtKeyBit()


class IndexPostListAPIView(ListAPIView):
    serializer_class = PostListSerializer
    queryset = Post.objects.all()
    pagination_class = PageNumberPagination
    permission_classes = [AllowAny]


class PostViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    博客文章视图集

    list:
    返回博客文章列表

    retrieve:
    返回博客文章详情

    list_comments:
    返回博客文章下的评论列表

    list_archive_dates:
    返回博客文章归档日期列表
    """

    serializer_class = PostListSerializer
    queryset = Post.objects.all()
    permission_classes = [AllowAny]
    serializer_class_table = {
        "list": PostListSerializer,
        "retrieve": PostRetrieveSerializer,
    }
    filter_backends = [DjangoFilterBackend]
    filterset_class = PostFilter

    def get_serializer_class(self):
        return self.serializer_class_table.get(
            self.action, super().get_serializer_class()
        )

    @cache_response(timeout=5 * 60, key_func=PostListKeyConstructor())
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @cache_response(timeout=5 * 60, key_func=PostObjectKeyConstructor())
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(responses={200: "归档日期列表，时间倒序排列。例如：['2020-08', '2020-06']。"})
    @action(
        methods=["GET"],
        detail=False,
        url_path="archive/dates",
        url_name="archive-date",
        filter_backends=None,
        pagination_class=None,
    )
    def list_archive_dates(self, request, *args, **kwargs):
        dates = Post.objects.dates("created_time", "month", order="DESC")
        date_field = DateField()
        data = [date_field.to_representation(date)[:7] for date in dates]
        return Response(data=data, status=status.HTTP_200_OK)

    @cache_response(timeout=5 * 60, key_func=CommentListKeyConstructor())
    @action(
        methods=["GET"],
        detail=True,
        url_path="comments",
        url_name="comment",
        filter_backends=None,  # 移除从 PostViewSet 自动继承的 filter_backends，这样 drf-yasg 就不会生成过滤参数
        suffix="List",  # 将这个 action 返回的结果标记为列表，否则 drf-yasg 会根据 detail=True 将结果误判为单个对象
        pagination_class=LimitOffsetPagination,
        serializer_class=CommentSerializer,
    )
    def list_comments(self, request, *args, **kwargs):
        # 根据 URL 传入的参数值（文章 id）获取到博客文章记录
        post = self.get_object()
        # 获取文章下关联的全部评论
        queryset = post.comment_set.all().order_by("-created_time")
        # 对评论列表进行分页，根据 URL 传入的参数获取指定页的评论
        page = self.paginate_queryset(queryset)
        # 序列化评论
        serializer = self.get_serializer(page, many=True)
        # 返回分页后的评论列表
        return self.get_paginated_response(serializer.data)


index = PostViewSet.as_view({"get": "list"})


class CategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    博客文章分类视图集

    list:
    返回博客文章分类列表
    """

    serializer_class = CategorySerializer
    # 关闭分页
    pagination_class = None

    def get_queryset(self):
        return Category.objects.all().order_by("name")


class TagViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    博客文章标签视图集

    list:
    返回博客文章标签列表
    """

    serializer_class = TagSerializer
    # 关闭分页
    pagination_class = None

    def get_queryset(self):
        return Tag.objects.all().order_by("name")


class PostSearchAnonRateThrottle(AnonRateThrottle):
    THROTTLE_RATES = {"anon": "5/min"}


class PostSearchFilterInspector(FilterInspector):
    def get_filter_parameters(self, filter_backend):
        return [
            openapi.Parameter(
                name="text",
                in_=openapi.IN_QUERY,
                required=True,
                description="搜索关键词",
                type=openapi.TYPE_STRING,
            )
        ]


@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        auto_schema=None,
    ),
)
# @method_decorator(
#     name="list",
#     decorator=swagger_auto_schema(
#         operation_description="返回关键词搜索结果",
#         filter_inspectors=[PostSearchFilterInspector],
#     ),
# )
class PostSearchView(HaystackViewSet):
    """
    搜索视图集

    list:
    返回搜索结果列表
    """

    index_models = [Post]
    serializer_class = PostHaystackSerializer
    throttle_classes = [PostSearchAnonRateThrottle]


class ApiVersionTestViewSet(viewsets.ViewSet):  # pragma: no cover
    swagger_schema = None

    @action(
        methods=["GET"],
        detail=False,
        url_path="test",
        url_name="test",
    )
    def test(self, request, *args, **kwargs):
        if request.version == "v1":
            return Response(
                data={
                    "version": request.version,
                    "warning": "该接口的 v1 版本已废弃，请尽快迁移至 v2 版本",
                }
            )
        return Response(data={"version": request.version})
