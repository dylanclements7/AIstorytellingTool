from django.urls import path
from . import views  # imports your view functions from main/views.py

urlpatterns = [
    path('', views.home, name='home'),
]
