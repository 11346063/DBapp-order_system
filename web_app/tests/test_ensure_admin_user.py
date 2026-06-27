from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase
from django.urls import reverse

from web_app.models import Identity, User


class EnsureAdminUserCommandTest(TestCase):
    def test_creates_admin_user_that_can_login_to_django_admin(self):
        out = StringIO()

        call_command(
            "ensure_admin_user",
            account="0912345678",
            password="pass12345",
            name="管理者",
            email="boss@example.com",
            stdout=out,
        )

        user = User.objects.get(account="0912345678")
        self.assertEqual(user.identity, Identity.ADMIN)
        self.assertTrue(user.status)
        self.assertEqual(user.phone_number, "0912345678")
        self.assertTrue(user.check_password("pass12345"))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertIn("Admin user created", out.getvalue())

        client = Client()
        self.assertTrue(client.login(username="0912345678", password="pass12345"))
        response = client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)

        response = client.get(reverse("web_app:staff_orders"))
        self.assertEqual(response.status_code, 200)

    def test_updates_existing_user_to_admin_and_resets_password(self):
        User.objects.create_user(
            account="0911111111",
            password="old-pass",
            name="顧客",
            identity=Identity.CUSTOMER,
            status=False,
        )

        out = StringIO()
        call_command(
            "ensure_admin_user",
            account="0911111111",
            password="new-pass",
            name="管理員",
            stdout=out,
        )

        user = User.objects.get(account="0911111111")
        self.assertEqual(user.identity, Identity.ADMIN)
        self.assertTrue(user.status)
        self.assertEqual(user.name, "管理員")
        self.assertTrue(user.check_password("new-pass"))
        self.assertIn("Admin user updated", out.getvalue())

    def test_existing_user_password_is_unchanged_when_password_not_provided(self):
        User.objects.create_user(
            account="0922222222",
            password="keep-pass",
            name="管理員",
            identity=Identity.ADMIN,
        )

        call_command("ensure_admin_user", account="0922222222", name="Still Admin")

        user = User.objects.get(account="0922222222")
        self.assertTrue(user.check_password("keep-pass"))
        self.assertEqual(user.name, "Still Admin")

    def test_new_user_requires_password(self):
        with self.assertRaises(CommandError):
            call_command("ensure_admin_user", account="0933333333")

    def test_account_must_be_phone_number_for_project_login(self):
        with self.assertRaises(CommandError):
            call_command(
                "ensure_admin_user",
                account="admin",
                password="pass12345",
            )

    def test_uses_environment_password_for_new_user(self):
        with patch.dict(
            "os.environ",
            {
                "DJANGO_SUPERUSER_ACCOUNT": "0944444444",
                "DJANGO_SUPERUSER_PASSWORD": "env-pass",
                "DJANGO_SUPERUSER_NAME": "Env Admin",
            },
        ):
            call_command("ensure_admin_user")

        user = User.objects.get(account="0944444444")
        self.assertEqual(user.identity, Identity.ADMIN)
        self.assertEqual(user.name, "Env Admin")
        self.assertTrue(user.check_password("env-pass"))
