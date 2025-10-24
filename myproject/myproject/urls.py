from django.contrib import admin
from django.urls import path, include  # include lets us connect to other URL files

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('main.urls')),  # route all URLs starting from / to the main app
]
