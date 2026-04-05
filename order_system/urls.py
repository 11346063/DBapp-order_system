from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from web_app.views.type import type_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),
    path('', include('web_app.urls')),
]
