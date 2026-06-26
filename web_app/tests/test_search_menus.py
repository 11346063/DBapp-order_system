"""
search_menus service 函式（services/menu.py）測試。

涵蓋：空 query、按 name/info/remark/type_name 搜尋、無結果、大小寫不敏感。
"""

from django.test import TestCase

from web_app.models import Menu, Type
from web_app.services import menu as menu_service


class SearchMenusTest(TestCase):
    def setUp(self):
        self.type_main = Type.objects.create(type_name="主餐")
        self.type_drink = Type.objects.create(type_name="飲料")

        self.chicken = Menu.objects.create(
            type=self.type_main,
            name="香脆炸雞",
            price=80,
            info="外皮酥脆",
            remark="可加辣",
        )
        self.pork = Menu.objects.create(
            type=self.type_main,
            name="里肌豬排",
            price=90,
            info="台式口味",
            remark="",
        )
        self.juice = Menu.objects.create(
            type=self.type_drink,
            name="鮮榨柳橙汁",
            price=60,
            info="新鮮現榨",
            remark="無糖可選",
        )

    def _search(self, query):
        qs = Menu.objects.select_related("type").all()
        return list(menu_service.search_menus(qs, query))

    # ------------------------------------------------------------------
    # 空 query → 回傳全部
    # ------------------------------------------------------------------

    def test_empty_string_returns_all(self):
        self.assertEqual(len(self._search("")), 3)

    def test_none_returns_all(self):
        self.assertEqual(len(self._search(None)), 3)

    # ------------------------------------------------------------------
    # 按各欄位搜尋
    # ------------------------------------------------------------------

    def test_matches_by_name(self):
        result = self._search("炸雞")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "香脆炸雞")

    def test_matches_by_info(self):
        result = self._search("台式口味")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "里肌豬排")

    def test_matches_by_remark(self):
        result = self._search("無糖可選")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "鮮榨柳橙汁")

    def test_matches_by_type_name(self):
        result = self._search("飲料")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "鮮榨柳橙汁")

    def test_partial_match_works(self):
        result = self._search("酥脆")  # 符合 info "外皮酥脆"

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "香脆炸雞")

    # ------------------------------------------------------------------
    # 無結果
    # ------------------------------------------------------------------

    def test_no_match_returns_empty_queryset(self):
        result = self._search("完全不存在的字串XYZ")

        self.assertEqual(result, [])

    # ------------------------------------------------------------------
    # 跨欄位：同一關鍵字符合多筆
    # ------------------------------------------------------------------

    def test_query_matching_multiple_items(self):
        result = self._search("主餐")  # 兩筆屬於主餐分類

        names = {m.name for m in result}
        self.assertIn("香脆炸雞", names)
        self.assertIn("里肌豬排", names)
        self.assertNotIn("鮮榨柳橙汁", names)
