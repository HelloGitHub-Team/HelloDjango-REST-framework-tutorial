import unittest

from blog.serializers import HighlightedCharField
from django.test import RequestFactory
from rest_framework.request import Request


class HighlightedCharFieldTestCase(unittest.TestCase):
    def test_to_representation(self):
        field = HighlightedCharField()
        request = RequestFactory().get("/", {"text": "关键词"})
        drf_request = Request(request=request)
        setattr(field, "_context", {"request": drf_request})
        document = "无关文本关键词无关文本，其他别的关键词别的无关的词。"
        result = field.to_representation(document)
        expected = (
            '无关文本<span class="highlighted">关键词</span>无关文本，'
            '其他别的<span class="highlighted">关键词</span>别的无关的词。'
        )
        self.assertEqual(result, expected)
