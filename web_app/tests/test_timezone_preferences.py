import json
from datetime import datetime

from django.conf import settings
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from web_app.utils.timezone import (
    convert_store_time_to_user_timezone,
    get_session_timezone,
    normalize_timezone,
    store_session_timezone,
)


class TimezoneUtilityTest(SimpleTestCase):
    def test_normalize_accepts_valid_iana_timezone(self):
        self.assertEqual(normalize_timezone("Asia/Tokyo"), "Asia/Tokyo")

    def test_normalize_rejects_invalid_timezone(self):
        with self.assertRaisesMessage(ValueError, "無效的時區"):
            normalize_timezone("Not/AZone")

    def test_missing_session_timezone_falls_back_to_settings_timezone(self):
        self.assertEqual(get_session_timezone({}), settings.TIME_ZONE)

    def test_naive_store_time_converts_from_store_timezone(self):
        converted = convert_store_time_to_user_timezone(
            datetime(2026, 6, 24, 12, 0), "Asia/Tokyo"
        )
        self.assertEqual(converted.strftime("%Y-%m-%d %H:%M"), "2026-06-24 13:00")

    def test_store_session_timezone_persists_normalized_value(self):
        session = {}
        timezone_name = store_session_timezone(session, "Asia/Tokyo")
        self.assertEqual(timezone_name, "Asia/Tokyo")
        self.assertEqual(session["timezone"], "Asia/Tokyo")


class TimezonePreferenceAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("web_app:v1_preferences_timezone")

    def test_post_valid_timezone_stores_session_value(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"timezone": "Asia/Tokyo"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["timezone"], "Asia/Tokyo")
        self.assertEqual(self.client.session["timezone"], "Asia/Tokyo")

    def test_post_invalid_timezone_returns_standard_validation_error(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"timezone": "Not/AZone"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("timezone", data["errors"])
