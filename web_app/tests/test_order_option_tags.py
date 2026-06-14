"""
A1：order-level 選項表現層（format_order_options / format_order_option_tags）。

這兩個函式為純函式（只讀取 option_link.opt.name / .opt.is_custom_extra / .level
與 settings 的 option_name_*），用 stub 物件做快速單元測試，不需要 DB。
此測試先固定（characterize）既有行為，作為重構安全網。
"""

from types import SimpleNamespace

from django.test import SimpleTestCase

from web_app.enums import SpicyLevel
from web_app.services import order as order_service

_SETTINGS = SimpleNamespace(
    option_name_spicy="辣度",
    option_name_garlic="加蒜",
    option_name_basil="九層塔",
)


def _opt(name, level, is_custom_extra=False):
    return SimpleNamespace(
        opt=SimpleNamespace(name=name, is_custom_extra=is_custom_extra),
        level=level,
    )


class FormatOrderOptionsTest(SimpleTestCase):
    def test_spicy_uses_spicy_level_label(self):
        raw = [_opt("辣度", SpicyLevel.HOT)]
        self.assertEqual(order_service.format_order_options(raw, _SETTINGS), "大辣")

    def test_garlic_and_basil_labels(self):
        raw = [_opt("加蒜", 2), _opt("九層塔", 1)]
        self.assertEqual(
            order_service.format_order_options(raw, _SETTINGS),
            "加蒜頭x2｜加九層塔x1",
        )

    def test_custom_extra_uses_name(self):
        raw = [_opt("起司", 1, is_custom_extra=True)]
        self.assertEqual(order_service.format_order_options(raw, _SETTINGS), "起司")

    def test_unknown_option_is_skipped(self):
        raw = [_opt("未知選項", 1), _opt("辣度", SpicyLevel.MILD)]
        self.assertEqual(order_service.format_order_options(raw, _SETTINGS), "小辣")

    def test_empty_returns_empty_string(self):
        self.assertEqual(order_service.format_order_options([], _SETTINGS), "")


class FormatOrderOptionTagsTest(SimpleTestCase):
    def test_spicy_none_has_custom_style(self):
        raw = [_opt("辣度", SpicyLevel.NONE)]
        tags = order_service.format_order_option_tags(raw, _SETTINGS)
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
        raw = [_opt("辣度", SpicyLevel.HOT)]
        tags = order_service.format_order_option_tags(raw, _SETTINGS)
        self.assertEqual(
            tags, [{"label": "大辣", "css": "bg-danger text-white", "style": ""}]
        )

    def test_garlic_and_basil_are_primary_badges(self):
        raw = [_opt("加蒜", 1), _opt("九層塔", 3)]
        tags = order_service.format_order_option_tags(raw, _SETTINGS)
        self.assertEqual(
            tags,
            [
                {"label": "加蒜頭x1", "css": "bg-primary text-white", "style": ""},
                {"label": "加九層塔x3", "css": "bg-primary text-white", "style": ""},
            ],
        )

    def test_custom_extra_is_success_badge(self):
        raw = [_opt("珍珠", 1, is_custom_extra=True)]
        tags = order_service.format_order_option_tags(raw, _SETTINGS)
        self.assertEqual(
            tags, [{"label": "珍珠", "css": "bg-success text-white", "style": ""}]
        )

    def test_unknown_option_is_skipped(self):
        raw = [_opt("未知選項", 1)]
        self.assertEqual(order_service.format_order_option_tags(raw, _SETTINGS), [])
