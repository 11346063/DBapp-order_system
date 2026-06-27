import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from web_app.models import Identity, User
from web_app.utils.phone import PhoneValidationError, normalize_tw_mobile


class Command(BaseCommand):
    help = "建立或更新可登入專案後台與 Django Admin 的管理員帳號。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--account",
            default=None,
            help=(
                "登入帳號，必須是台灣手機號碼。未提供時依序讀取 "
                "DJANGO_SUPERUSER_ACCOUNT、ADMIN_ACCOUNT、--phone。"
            ),
        )
        parser.add_argument(
            "--password",
            default=None,
            help=(
                "登入密碼。可改用環境變數 DJANGO_SUPERUSER_PASSWORD 或 "
                "ADMIN_PASSWORD。新帳號必填；既有帳號不提供則不變更密碼。"
            ),
        )
        parser.add_argument(
            "--name",
            default=None,
            help="顯示名稱。未提供時依序讀取 DJANGO_SUPERUSER_NAME、ADMIN_NAME，最後使用帳號。",
        )
        parser.add_argument("--email", default="", help="Email，可省略。")
        parser.add_argument("--phone", default="", help="電話；未提供時使用帳號。")

    @transaction.atomic
    def handle(self, *args, **options):
        account = (
            options["account"]
            or os.environ.get("DJANGO_SUPERUSER_ACCOUNT")
            or os.environ.get("ADMIN_ACCOUNT")
            or options["phone"]
        )
        if not account:
            raise CommandError(
                "請提供 --account <台灣手機號碼>，"
                "或設定 DJANGO_SUPERUSER_ACCOUNT / ADMIN_ACCOUNT。"
            )
        try:
            account = normalize_tw_mobile(account)
        except PhoneValidationError as exc:
            raise CommandError(
                "管理員帳號必須是台灣手機號碼，才能同時登入專案後台與 Django Admin。"
            ) from exc
        phone_number = account
        if options["phone"]:
            try:
                phone_number = normalize_tw_mobile(options["phone"])
            except PhoneValidationError as exc:
                raise CommandError("電話必須是有效的台灣手機號碼。") from exc

        password = (
            options["password"]
            or os.environ.get("DJANGO_SUPERUSER_PASSWORD")
            or os.environ.get("ADMIN_PASSWORD")
        )
        name = (
            options["name"]
            or os.environ.get("DJANGO_SUPERUSER_NAME")
            or os.environ.get("ADMIN_NAME")
            or account
        )

        user = User.objects.filter(account=account).first()
        created = user is None

        if created and not password:
            raise CommandError(
                "建立新管理員帳號必須提供 --password，"
                "或設定 DJANGO_SUPERUSER_PASSWORD / ADMIN_PASSWORD。"
            )

        if created:
            user = User(account=account)

        user.name = name
        user.identity = Identity.ADMIN
        user.status = True
        if options["email"]:
            user.email = options["email"]
        user.phone_number = phone_number
        if password:
            user.set_password(password)
        user.save()

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Admin user {action}: account={user.account}, identity={user.identity}"
            )
        )
