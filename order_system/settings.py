from pathlib import Path
import os

from django.contrib.messages import constants as messages_constants
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

AUTH_USER_MODEL = "web_app.User"


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-0gctfk#au@1l-&#&0u88hlc_fwpo3)(ly=o2&i*z6hw)u0)n8l"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1", "http://localhost"]


# Application definition

INSTALLED_APPS = [
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
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

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

load_dotenv()

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

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_URL = "/login/"


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
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": __import__("datetime").timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": __import__("datetime").timedelta(days=7),
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
        "{ \"status\": \"success\", \"message\": \"操作成功\", \"data\": { ... } }\n"
        "// 失敗\n"
        "{ \"status\": \"error\", \"message\": \"錯誤原因\" }\n"
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
