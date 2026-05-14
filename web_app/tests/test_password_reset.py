import re

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from web_app.models import User


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            account="reset_user",
            password="old-pass-123",
            name="密碼重設使用者",
            email="reset@example.com",
        )

    def test_login_page_links_to_password_reset(self):
        response = self.client.get(reverse("web_app:login"))

        self.assertContains(response, reverse("web_app:password_reset"))
        self.assertContains(response, "忘記密碼")

    def test_password_reset_sends_email_for_registered_email(self):
        response = self.client.post(
            reverse("web_app:password_reset"),
            {"email": "reset@example.com"},
        )

        self.assertRedirects(response, reverse("web_app:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("密碼重設", mail.outbox[0].subject)
        self.assertIn("/password-reset/", mail.outbox[0].body)

    def test_password_reset_does_not_send_email_for_unknown_email(self):
        response = self.client.post(
            reverse("web_app:password_reset"),
            {"email": "missing@example.com"},
        )

        self.assertRedirects(response, reverse("web_app:password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_does_not_send_email_for_account_without_email(self):
        User.objects.create_user(
            account="no_email_user",
            password="old-pass-123",
            name="無信箱使用者",
        )

        response = self.client.post(
            reverse("web_app:password_reset"),
            {"email": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_token_updates_password(self):
        self.client.post(
            reverse("web_app:password_reset"),
            {"email": "reset@example.com"},
        )
        reset_path = re.search(
            r"/password-reset/[^/\s]+/[^/\s]+/",
            mail.outbox[0].body,
        ).group(0)

        token_response = self.client.get(reset_path)
        self.assertEqual(token_response.status_code, 302)

        set_password_path = token_response["Location"]
        response = self.client.post(
            set_password_path,
            {
                "new_password1": "new-pass-12345",
                "new_password2": "new-pass-12345",
            },
        )

        self.assertRedirects(response, reverse("web_app:password_reset_complete"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-pass-12345"))
