from django.urls import path
from . import views  # imports your view functions from main/views.py

urlpatterns = [
    path('', views.idea, name='idea'),
    path('draft/', views.draft, name='draft'),
    path('personas/', views.personas, name='personas'),
    path('locations/', views.locations, name='locations'),
    path('scene1/', views.scene1, name='scene1'),
    path('scene2/', views.scene2, name='scene2'),
    path('scene3/', views.scene3, name='scene3'),
    path('scene4/', views.scene4, name='scene4'),
    path('scene5/', views.scene5, name='scene5'),
    path('scene6/', views.scene6, name='scene6'),
    path('video/', views.video, name='video'),
]
