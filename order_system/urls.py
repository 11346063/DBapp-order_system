from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from web_app.views.type import type_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('', include('web_app.urls')),
]
