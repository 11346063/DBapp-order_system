"""
Google OAuth 登入流程測試。
外部 HTTP 呼叫（httpx.AsyncClient）全部 mock，不需要網路。
"""

from unittest.mock import AsyncMock, MagicMock, patch

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


def _mock_httpx_client(token_resp, info_resp=None):
    """回傳一個可作為 async with httpx.AsyncClient() 使用的 mock。

    用 MagicMock 作為 client，明確設定 __aenter__ 回傳自身，
    確保 async with 拿到的 client 是我們設定好 post/get 的那個物件。
    """
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=token_resp)
    if info_resp is not None:
        mock_client.get = AsyncMock(return_value=info_resp)
    return mock_client


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

    @patch("web_app.views.oauth_views.httpx.AsyncClient")
    def test_new_google_user_created_and_redirected_to_phone_required(self, MockClient):
        MockClient.return_value = _mock_httpx_client(
            _make_token_response(),
            _make_userinfo_response(sub="newuser_sub_001"),
        )

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

    @patch("web_app.views.oauth_views.httpx.AsyncClient")
    def test_existing_google_user_with_phone_logs_in_directly(self, MockClient):
        user = User.objects.create_user(
            account="google_existingsub",
            password=None,
            name="Existing",
            phone_number="0912000000",
            auth_provider="google",
            google_sub="existing_sub_999",
            identity=Identity.CUSTOMER,
        )
        MockClient.return_value = _mock_httpx_client(
            _make_token_response(),
            _make_userinfo_response(sub="existing_sub_999"),
        )

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

    @patch("web_app.views.oauth_views.httpx.AsyncClient")
    def test_token_exchange_failure_redirects_to_login(self, MockClient):
        import httpx as httpx_lib

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(
            side_effect=httpx_lib.RequestError("network error")
        )
        MockClient.return_value = mock_client

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


class GoogleOAuthCallbackEdgeCaseTest(TestCase):
    def setUp(self):
        session = self.client.session
        session["oauth_state"] = "valid_state"
        session.save()

    def _callback_url(self, **params):
        base = reverse("web_app:google_oauth_callback")
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base}?{query}"

    @patch("web_app.views.oauth_views.httpx.AsyncClient")
    def test_userinfo_without_sub_redirects_to_login(self, MockClient):
        MockClient.return_value = _mock_httpx_client(
            _make_token_response(),
            _make_userinfo_response(sub=""),
        )
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

    @patch("web_app.views.oauth_views.httpx.AsyncClient")
    def test_open_redirect_next_is_ignored(self, MockClient):
        User.objects.create_user(
            account="google_redirsub",
            password=None,
            name="Redir",
            phone_number="0912000111",
            auth_provider="google",
            google_sub="redir_sub_001",
            identity=Identity.CUSTOMER,
        )
        MockClient.return_value = _mock_httpx_client(
            _make_token_response(),
            _make_userinfo_response(sub="redir_sub_001"),
        )
        with self.settings(
            GOOGLE_OAUTH2_CLIENT_ID="cid",
            GOOGLE_OAUTH2_CLIENT_SECRET="csec",
            GOOGLE_OAUTH2_REDIRECT_URI="http://localhost/cb/",
        ):
            response = self.client.get(
                self._callback_url(
                    state="valid_state", code="authcode", next="http://evil.com"
                )
            )
        self.assertNotIn("evil.com", response["Location"])
        self.assertRedirects(
            response, reverse("web_app:home"), fetch_redirect_response=False
        )

    @patch("web_app.views.oauth_views.httpx.AsyncClient")
    def test_state_cannot_be_replayed(self, MockClient):
        User.objects.create_user(
            account="google_replaysub",
            password=None,
            name="Replay",
            phone_number="0912000222",
            auth_provider="google",
            google_sub="replay_sub_001",
            identity=Identity.CUSTOMER,
        )
        MockClient.return_value = _mock_httpx_client(
            _make_token_response(),
            _make_userinfo_response(sub="replay_sub_001"),
        )
        settings_ctx = self.settings(
            GOOGLE_OAUTH2_CLIENT_ID="cid",
            GOOGLE_OAUTH2_CLIENT_SECRET="csec",
            GOOGLE_OAUTH2_REDIRECT_URI="http://localhost/cb/",
        )
        with settings_ctx:
            first = self.client.get(
                self._callback_url(state="valid_state", code="authcode")
            )
            self.assertRedirects(
                first, reverse("web_app:home"), fetch_redirect_response=False
            )
            # state 已於第一次 callback 後 pop，重放應失敗
            second = self.client.get(
                self._callback_url(state="valid_state", code="authcode")
            )
        self.assertRedirects(
            second, reverse("web_app:login"), fetch_redirect_response=False
        )


class CreateGoogleUserTest(TestCase):
    def test_account_collision_appends_suffix(self):
        from web_app.views.oauth_views import _create_google_user

        google_sub = "1234567890123"
        User.objects.create_user(
            account="google_1234567890123",
            password=None,
            name="Existing",
            identity=Identity.CUSTOMER,
        )

        user = _create_google_user(google_sub=google_sub, email=None, name="New")

        self.assertEqual(user.google_sub, google_sub)
        self.assertEqual(user.account, "google_1234567890_1")


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
