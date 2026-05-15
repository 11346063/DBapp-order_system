from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.renderers import OpenApiJsonRenderer
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("captcha/", include("captcha.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    # JWT 認證
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # API 文件
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/openapi.json",
        SpectacularAPIView.as_view(renderer_classes=[OpenApiJsonRenderer]),
        name="schema-json",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger_ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # 主應用
    path("", include("web_app.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
