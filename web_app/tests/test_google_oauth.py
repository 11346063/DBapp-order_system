"""
Google OAuth 登入流程測試。
外部 HTTP 呼叫（requests.post / requests.get）全部 mock，不需要網路。
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse

from web_app.models import Identity, User


def _make_token_response(access_token="fake_access_token"):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"access_token": access_token}
    resp.raise_for_status.return_value = None
    return resp


def _make_userinfo_response(
    sub="12345678901234567890", email="test@gmail.com", name="Test User"
):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"sub": sub, "email": email, "name": name}
    resp.raise_for_status.return_value = None
    return resp


class GoogleOAuthInitiateTest(TestCase):
    def test_redirects_to_google(self):
        with self.settings(
            GOOGLE_OAUTH2_CLIENT_ID="test-client-id",
            GOOGLE_OAUTH2_REDIRECT_URI="http://localhost/oauth/google/callback/",
        ):
            response = self.client.get(reverse("web_app:google_oauth_initiate"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response["Location"])
        self.assertIn("test-client-id", response["Location"])

    def test_stores_state_in_session(self):
        with self.settings(
            GOOGLE_OAUTH2_CLIENT_ID="test-client-id",
            GOOGLE_OAUTH2_REDIRECT_URI="http://localhost/oauth/google/callback/",
        ):
            self.client.get(reverse("web_app:google_oauth_initiate"))
        self.assertIn("oauth_state", self.client.session)

    def test_authenticated_user_redirects_to_home(self):
        user = User.objects.create_user(
            account="0912345678",
            password="pass",
            name="Test",
            identity=Identity.CUSTOMER,
        )
        self.client.force_login(user)
        response = self.client.get(reverse("web_app:google_oauth_initiate"))
        self.assertRedirects(
            response, reverse("web_app:home"), fetch_redirect_response=False
        )


class GoogleOAuthCallbackTest(TestCase):
    def setUp(self):
        session = self.client.session
        session["oauth_state"] = "valid_state"
        session.save()

    def _callback_url(self, **params):
        base = reverse("web_app:google_oauth_callback")
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base}?{query}"

    def test_invalid_state_redirects_to_login(self):
        response = self.client.get(
            self._callback_url(state="wrong_state", code="somecode")
        )
        self.assertRedirects(
            response, reverse("web_app:login"), fetch_redirect_response=False
        )

    def test_missing_state_redirects_to_login(self):
        response = self.client.get(self._callback_url(code="somecode"))
        self.assertRedirects(
            response, reverse("web_app:login"), fetch_redirect_response=False
        )

    def test_google_error_param_redirects_to_login(self):
        response = self.client.get(
            self._callback_url(state="valid_state", error="access_denied")
        )
        self.assertRedirects(
            response, reverse("web_app:login"), fetch_redirect_response=False
        )

    @patch("web_app.views.oauth_views.requests.get")
    @patch("web_app.views.oauth_views.requests.post")
    def test_new_google_user_created_and_redirected_to_phone_required(
        self, mock_post, mock_get
    ):
        mock_post.return_value = _make_token_response()
        mock_get.return_value = _make_userinfo_response(sub="newuser_sub_001")

        with self.settings(
            GOOGLE_OAUTH2_CLIENT_ID="cid",
            GOOGLE_OAUTH2_CLIENT_SECRET="csec",
            GOOGLE_OAUTH2_REDIRECT_URI="http://localhost/cb/",
        ):
            response = self.client.get(
                self._callback_url(state="valid_state", code="authcode")
            )

        self.assertTrue(User.objects.filter(google_sub="newuser_sub_001").exists())
        self.assertRedirects(
            response,
            reverse("web_app:oauth_phone_required"),
            fetch_redirect_response=False,
        )

    @patch("web_app.views.oauth_views.requests.get")
    @patch("web_app.views.oauth_views.requests.post")
    def test_existing_google_user_with_phone_logs_in_directly(
        self, mock_post, mock_get
    ):
        user = User.objects.create_user(
            account="google_existingsub",
            password=None,
            name="Existing",
            phone_number="0912000000",
            auth_provider="google",
            google_sub="existing_sub_999",
            identity=Identity.CUSTOMER,
        )
        mock_post.return_value = _make_token_response()
        mock_get.return_value = _make_userinfo_response(sub="existing_sub_999")

        with self.settings(
            GOOGLE_OAUTH2_CLIENT_ID="cid",
            GOOGLE_OAUTH2_CLIENT_SECRET="csec",
            GOOGLE_OAUTH2_REDIRECT_URI="http://localhost/cb/",
        ):
            response = self.client.get(
                self._callback_url(state="valid_state", code="authcode")
            )

        self.assertRedirects(
            response, reverse("web_app:home"), fetch_redirect_response=False
        )
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    @patch("web_app.views.oauth_views.requests.post")
    def test_token_exchange_failure_redirects_to_login(self, mock_post):
        import requests as req_lib

        mock_post.side_effect = req_lib.RequestException("network error")

        with self.settings(
            GOOGLE_OAUTH2_CLIENT_ID="cid",
            GOOGLE_OAUTH2_CLIENT_SECRET="csec",
            GOOGLE_OAUTH2_REDIRECT_URI="http://localhost/cb/",
        ):
            response = self.client.get(
                self._callback_url(state="valid_state", code="authcode")
            )

        self.assertRedirects(
            response, reverse("web_app:login"), fetch_redirect_response=False
        )


class OAuthPhoneRequiredTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            account="google_phonetest",
            password=None,
            name="Phone User",
            auth_provider="google",
            google_sub="phone_sub_001",
            identity=Identity.CUSTOMER,
        )
        session = self.client.session
        session["oauth_pending_user_id"] = self.user.pk
        session.save()

    def test_get_renders_form(self):
        response = self.client.get(reverse("web_app:oauth_phone_required"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/oauth_phone_required.html")

    def test_no_session_redirects_to_login(self):
        session = self.client.session
        del session["oauth_pending_user_id"]
        session.save()
        response = self.client.get(reverse("web_app:oauth_phone_required"))
        self.assertRedirects(
            response, reverse("web_app:login"), fetch_redirect_response=False
        )

    def test_valid_phone_saves_and_logs_in(self):
        response = self.client.post(
            reverse("web_app:oauth_phone_required"),
            {"phone_number": "0912345678"},
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, "0912345678")
        self.assertRedirects(
            response, reverse("web_app:home"), fetch_redirect_response=False
        )
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_invalid_phone_shows_error(self):
        response = self.client.post(
            reverse("web_app:oauth_phone_required"),
            {"phone_number": "notaphone"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "有效的台灣手機號碼")
        self.user.refresh_from_db()
        self.assertIsNone(self.user.phone_number)

    def test_phone_normalization(self):
        self.client.post(
            reverse("web_app:oauth_phone_required"),
            {"phone_number": "+886912345678"},
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, "0912345678")
