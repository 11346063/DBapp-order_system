import secrets
from urllib.parse import urlencode

import httpx
from asgiref.sync import sync_to_async
from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _

from web_app.models import Identity, User
from web_app.utils.phone import PhoneValidationError, normalize_tw_mobile

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
_GOOGLE_SCOPES = "openid email profile"


def google_oauth_initiate(request):
    if request.user.is_authenticated:
        return redirect("web_app:home")

    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state

    params = urlencode(
        {
            "client_id": django_settings.GOOGLE_OAUTH2_CLIENT_ID,
            "redirect_uri": django_settings.GOOGLE_OAUTH2_REDIRECT_URI,
            "response_type": "code",
            "scope": _GOOGLE_SCOPES,
            "state": state,
            "access_type": "online",
        }
    )
    return redirect(f"{_GOOGLE_AUTH_URL}?{params}")


async def google_oauth_callback(request):
    # Session 第一次存取會懶載入（sync DB），先在 thread 中強制載入，之後都是記憶體操作
    await sync_to_async(lambda: request.session.keys())()

    state = request.GET.get("state")
    stored_state = request.session.pop("oauth_state", None)

    if not state or state != stored_state:
        messages.error(request, _("登入驗證失敗，請重試"))
        return redirect("web_app:login")

    if request.GET.get("error"):
        messages.error(request, _("Google 登入已取消"))
        return redirect("web_app:login")

    code = request.GET.get("code")
    if not code:
        messages.error(request, _("Google 登入失敗，請重試"))
        return redirect("web_app:login")

    # 非同步 HTTP：兩個請求依序執行（token → userinfo），不阻塞 event loop
    try:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                _GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": django_settings.GOOGLE_OAUTH2_CLIENT_ID,
                    "client_secret": django_settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                    "redirect_uri": django_settings.GOOGLE_OAUTH2_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
                timeout=10,
            )
            token_resp.raise_for_status()
            access_token = token_resp.json().get("access_token")

            info_resp = await client.get(
                _GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            info_resp.raise_for_status()
    except httpx.HTTPStatusError:
        messages.error(request, _("Google 登入失敗，請重試"))
        return redirect("web_app:login")
    except httpx.RequestError:
        messages.error(request, _("Google 登入失敗，請重試"))
        return redirect("web_app:login")

    userinfo = info_resp.json()
    google_sub = userinfo.get("sub")
    if not google_sub:
        messages.error(request, _("Google 帳號資料不完整，請重試"))
        return redirect("web_app:login")

    user = await User.objects.filter(google_sub=google_sub).afirst()
    if user is None:
        user = await sync_to_async(_create_google_user)(
            google_sub=google_sub,
            email=userinfo.get("email") or None,
            name=userinfo.get("name") or "顧客",
        )

    if not user.phone_number:
        request.session["oauth_pending_user_id"] = user.pk
        return redirect("web_app:oauth_phone_required")

    await sync_to_async(_complete_google_login)(request, user)
    next_url = request.GET.get("next", "")
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        next_url = ""
    return redirect(next_url or "web_app:home")


def oauth_phone_required(request):
    user_id = request.session.get("oauth_pending_user_id")
    if not user_id:
        return redirect("web_app:login")

    user = User.objects.filter(pk=user_id).first()
    if user is None:
        return redirect("web_app:login")

    error = None
    if request.method == "POST":
        phone_raw = request.POST.get("phone_number", "").strip()
        try:
            phone = normalize_tw_mobile(phone_raw)
        except PhoneValidationError:
            error = _("請輸入有效的台灣手機號碼（例：0912345678）")
        else:
            user.phone_number = phone
            user.save(update_fields=["phone_number", "updated_at"])
            request.session.pop("oauth_pending_user_id", None)
            _complete_google_login(request, user)
            return redirect("web_app:home")

    return render(request, "auth/oauth_phone_required.html", {"error": error})


def _create_google_user(*, google_sub, email, name):
    base_account = f"google_{google_sub[-13:]}"[:20]
    account = base_account
    suffix = 0
    while User.objects.filter(account=account).exists():
        suffix += 1
        account = f"{base_account[:17]}_{suffix}"

    return User.objects.create_user(
        account=account,
        password=None,
        name=name,
        email=email,
        auth_provider="google",
        google_sub=google_sub,
        identity=Identity.CUSTOMER,
    )


def _complete_google_login(request, user):
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    messages.success(request, _("歡迎，{name}！").format(name=user.name))
