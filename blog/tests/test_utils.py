import unittest
from datetime import datetime

from django.core.cache import cache

from ..utils import Highlighter, UpdatedAtKeyBit


class HighlighterTestCase(unittest.TestCase):
    def test_highlight(self):
        document = "这是一个比较长的标题，用于测试关键词高亮但不被截断。"
        highlighter = Highlighter("标题")
        expected = '这是一个比较长的<span class="highlighted">标题</span>，用于测试关键词高亮但不被截断。'
        self.assertEqual(highlighter.highlight(document), expected)

        highlighter = Highlighter("关键词高亮")
        expected = '这是一个比较长的标题，用于测试<span class="highlighted">关键词高亮</span>但不被截断。'
        self.assertEqual(highlighter.highlight(document), expected)

        highlighter = Highlighter("标题")
        document = "这是一个长度超过 200 的标题，应该被截断。" + "HelloDjangoTutorial" * 200
        self.assertTrue(
            highlighter.highlight(document).startswith(
                '...<span class="highlighted">标题</span>，应该被截断。'
            )
        )


class UpdatedAtKeyBitTestCase(unittest.TestCase):
    def test_get_data(self):
        # 未缓存的情况
        key_bit = UpdatedAtKeyBit()
        data = key_bit.get_data()
        self.assertEqual(data, str(cache.get(key_bit.key)))

        # 已缓存的情况
        cache.clear()
        now = datetime.utcnow()
        now_str = str(now)
        cache.set(key_bit.key, now)
        self.assertEqual(key_bit.get_data(), now_str)
