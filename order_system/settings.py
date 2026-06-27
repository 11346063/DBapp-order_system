from datetime import timedelta
from pathlib import Path
import os

from django.contrib.messages import constants as messages_constants
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

AUTH_USER_MODEL = "web_app.User"


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

_secret_key = os.getenv("DJANGO_SECRET_KEY", "")
_debug = os.getenv("DEBUG", "False") == "True"

if not _secret_key:
    if _debug:
        _secret_key = "django-insecure-fallback-only-for-dev"
    else:
        raise RuntimeError("DJANGO_SECRET_KEY must be set in production (DEBUG=False)")

SECRET_KEY = _secret_key
DEBUG = _debug

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Clickjacking 防護（XFrameOptionsMiddleware 預設即為 DENY，此處顯式宣告）
X_FRAME_OPTIONS = "DENY"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS", "http://127.0.0.1,http://localhost"
).split(",")


# Application definition

INSTALLED_APPS = [
    "daphne",
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "captcha",
    "web_app",
    "channels",
    "rest_framework",
    "drf_spectacular",
    "import_export",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "web_app.middleware.request_logging.RequestLoggingMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ENABLE_REQUEST_LOGGING = os.getenv("ENABLE_REQUEST_LOGGING", "False") == "True"

# 出單機列印代理驗證 token（店內代理以 X-Print-Token header 帶入）
PRINT_AGENT_TOKEN = os.getenv("PRINT_AGENT_TOKEN", "")

ROOT_URLCONF = "order_system.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "web_app/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "web_app.context_processors.cart_count",
            ],
        },
    },
]

WSGI_APPLICATION = "order_system.wsgi.application"
ASGI_APPLICATION = "order_system.asgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DB_SETTING = os.getenv("DB_ACCOUNT")
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "zh-hant"
LANGUAGES = [
    ("zh-hant", "繁體中文"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

# settings.py
TIME_ZONE = "Asia/Taipei"
USE_I18N = True
USE_TZ = False

SESSION_COOKIE_AGE = 10 * 60

SESSION_SAVE_EVERY_REQUEST = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "web_app/static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_URL = "/login/"

GOOGLE_OAUTH2_CLIENT_ID = os.getenv("GOOGLE_OAUTH2_CLIENT_ID", "")
GOOGLE_OAUTH2_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH2_CLIENT_SECRET", "")
GOOGLE_OAUTH2_REDIRECT_URI = os.getenv(
    "GOOGLE_OAUTH2_REDIRECT_URI", "http://localhost:8000/oauth/google/callback/"
)


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER or "noreply@example.com",
)

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Jazzmin ────────────────────────────────────────────────────────────────────

JAZZMIN_SETTINGS = {
    "site_title": "餐飲後台管理",
    "site_header": "餐飲系統",
    "site_brand": "DBapp",
    "welcome_sign": "歡迎回來，管理員",
    "copyright": "DBapp-menu",
    # 頂部搜尋欄預設搜尋 User
    "search_model": ["web_app.user", "web_app.order"],
    # 側欄 icon（對應 Font Awesome 5 class）
    "icons": {
        "web_app.order": "fas fa-receipt",
        "web_app.orderitem": "fas fa-list",
        "web_app.menu": "fas fa-utensils",
        "web_app.type": "fas fa-tags",
        "web_app.options": "fas fa-sliders-h",
        "web_app.optgroup": "fas fa-layer-group",
        "web_app.user": "fas fa-users",
        "web_app.storesettings": "fas fa-cog",
        "web_app.printjob": "fas fa-print",
        "auth.group": "fas fa-shield-alt",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    # 側欄固定（不隨捲動消失）
    "navigation_expanded": True,
    # 自訂側欄選單順序與分組
    "order_with_respect_to": [
        "web_app.order",
        "web_app.orderitem",
        "web_app.printjob",
        "web_app.menu",
        "web_app.type",
        "web_app.options",
        "web_app.optgroup",
        "web_app.user",
        "web_app.storesettings",
        "auth",
    ],
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-teal",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-teal",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

# Messages tags mapping for Bootstrap alert classes

MESSAGE_TAGS = {
    messages_constants.ERROR: "danger",
}

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "web_app.api.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "USER_ID_FIELD": "pk",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "絕佳食雞 API",
    "DESCRIPTION": (
        "台式炸物店「絕佳食雞」線上點餐系統 RESTful API。\n\n"
        "## 認證方式\n"
        "大多數寫入 API 需要 JWT Bearer Token。\n"
        "1. 呼叫 `POST /api/token/` 取得 `access` token（有效期 30 分鐘）與 `refresh` token（有效期 7 天）。\n"
        "2. 在後續請求的 Header 加上 `Authorization: Bearer <access_token>`。\n"
        "3. access token 過期後，呼叫 `POST /api/token/refresh/` 換發新 token。\n\n"
        "## 身份等級\n"
        "| identity | 說明 | 可用 API |\n"
        "|----------|------|----------|\n"
        "| `A` 管理員 | 最高權限 | 全部 |\n"
        "| `E` 員工 | 操作訂單、切換餐點 | 菜單切換、訂單狀態 |\n"
        "| `C` 顧客 | 一般使用者 | 購物車、再次訂購 |\n"
        "| `G` 訪客 | 未登入 | 僅讀取菜單、購物車 |\n\n"
        "## 統一回應格式\n"
        "```json\n"
        "// 成功\n"
        '{ "status": "success", "message": "操作成功", "data": { ... } }\n'
        "// 失敗\n"
        '{ "status": "error", "message": "錯誤原因" }\n'
        "```"
    ),
    "VERSION": "1.0.0",
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {"name": "菜單", "description": "菜單查詢與管理（建立、更新、上下架切換）"},
        {"name": "購物車", "description": "以 server-side session 管理的購物車操作"},
        {"name": "訂單", "description": "訂單狀態管理與再次訂購"},
    ],
    "SWAGGER_UI_SETTINGS": {
        "defaultModelsExpandDepth": 5,
        "defaultModelExpandDepth": 5,
        "displayRequestDuration": True,
        "filter": True,
    },
    "ENUM_GENERATE_CHOICE_DESCRIPTION": False,
}

# --- Logging ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file_app": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": BASE_DIR / "logs" / "app.log",
            "when": "midnight",
            "backupCount": 30,
            "encoding": "utf-8",
            "formatter": "verbose",
            "delay": True,
        },
        "file_error": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": BASE_DIR / "logs" / "error.log",
            "when": "midnight",
            "backupCount": 30,
            "encoding": "utf-8",
            "formatter": "verbose",
            "level": "ERROR",
            "delay": True,
        },
    },
    "root": {
        "handlers": ["console"] if DEBUG else ["console", "file_app", "file_error"],
        "level": "WARNING",
    },
    "loggers": {
        "web_app": {
            "handlers": ["console"] if DEBUG else ["console", "file_app", "file_error"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"] if DEBUG else ["file_error"],
            "level": "ERROR",
            "propagate": False,
        },
        # SQL query log — Django only emits these calls when DEBUG=True,
        # so the empty-handlers guard in prod is a belt-and-suspenders measure.
        "django.db.backends": {
            "handlers": ["console"] if DEBUG else [],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
