"""
A1：order-level 選項表現層（format_order_options / format_order_option_tags）。

這兩個函式為純函式（只讀取 option_link.opt_id / .opt.is_custom_extra / .level），
用 stub 物件做快速單元測試，不需要 DB。
此測試先固定（characterize）既有行為，作為重構安全網。
"""

from types import SimpleNamespace

from django.test import SimpleTestCase

from web_app.constants import BASIL_OPTION_ID, GARLIC_OPTION_ID, SPICY_OPTION_ID
from web_app.enums import SpicyLevel
from web_app.services import order as order_service


def _opt(opt_id, level, is_custom_extra=False, name=""):
    return SimpleNamespace(
        opt_id=opt_id,
        opt=SimpleNamespace(name=name, is_custom_extra=is_custom_extra),
        level=level,
    )


class FormatOrderOptionsTest(SimpleTestCase):
    def test_spicy_uses_spicy_level_label(self):
        raw = [_opt(SPICY_OPTION_ID, SpicyLevel.HOT)]
        self.assertEqual(order_service.format_order_options(raw), "大辣")

    def test_garlic_and_basil_labels(self):
        raw = [_opt(GARLIC_OPTION_ID, 2), _opt(BASIL_OPTION_ID, 1)]
        self.assertEqual(
            order_service.format_order_options(raw),
            "加蒜頭x2｜加九層塔x1",
        )

    def test_custom_extra_uses_name(self):
        raw = [_opt(99, 1, is_custom_extra=True, name="起司")]
        self.assertEqual(order_service.format_order_options(raw), "起司")

    def test_unknown_option_is_skipped(self):
        raw = [_opt(99, 1), _opt(SPICY_OPTION_ID, SpicyLevel.MILD)]
        self.assertEqual(order_service.format_order_options(raw), "小辣")

    def test_empty_returns_empty_string(self):
        self.assertEqual(order_service.format_order_options([]), "")


class FormatOrderOptionTagsTest(SimpleTestCase):
    def test_spicy_none_has_custom_style(self):
        raw = [_opt(SPICY_OPTION_ID, SpicyLevel.NONE)]
        tags = order_service.format_order_option_tags(raw)
        self.assertEqual(
            tags,
            [
                {
                    "label": "不辣",
                    "css": "text-white",
                    "style": "background-color:#9a7200;",
                }
            ],
        )

    def test_spicy_hot_is_danger_badge(self):
        raw = [_opt(SPICY_OPTION_ID, SpicyLevel.HOT)]
        tags = order_service.format_order_option_tags(raw)
        self.assertEqual(
            tags, [{"label": "大辣", "css": "bg-danger text-white", "style": ""}]
        )

    def test_garlic_and_basil_are_primary_badges(self):
        raw = [_opt(GARLIC_OPTION_ID, 1), _opt(BASIL_OPTION_ID, 3)]
        tags = order_service.format_order_option_tags(raw)
        self.assertEqual(
            tags,
            [
                {"label": "加蒜頭x1", "css": "bg-primary text-white", "style": ""},
                {"label": "加九層塔x3", "css": "bg-primary text-white", "style": ""},
            ],
        )

    def test_custom_extra_is_success_badge(self):
        raw = [_opt(99, 1, is_custom_extra=True, name="珍珠")]
        tags = order_service.format_order_option_tags(raw)
        self.assertEqual(
            tags, [{"label": "珍珠", "css": "bg-success text-white", "style": ""}]
        )

    def test_unknown_option_is_skipped(self):
        raw = [_opt(99, 1)]
        self.assertEqual(order_service.format_order_option_tags(raw), [])
