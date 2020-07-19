from datetime import datetime

from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.utils import timezone


class Comment(models.Model):
    name = models.CharField("名字", max_length=50)
    email = models.EmailField("邮箱")
    url = models.URLField("网址", blank=True)
    text = models.TextField("内容")
    created_time = models.DateTimeField("创建时间", default=timezone.now)
    post = models.ForeignKey("blog.Post", verbose_name="文章", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = verbose_name
        ordering = ["-created_time"]

    def __str__(self):
        return "{}: {}".format(self.name, self.text[:20])


def change_comment_updated_at(sender=None, instance=None, *args, **kwargs):
    cache.set("comment_updated_at", datetime.utcnow())


post_save.connect(receiver=change_comment_updated_at, sender=Comment)
post_delete.connect(receiver=change_comment_updated_at, sender=Comment)
