from django.urls import path, include

urlpatterns = [
    path("captcha/", include("captcha.urls")),
    path("", include("web_app.urls")),
]
