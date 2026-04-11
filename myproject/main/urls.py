from django.urls import path
from . import views  

urlpatterns = [
    path('', views.participant, name='participant'),
    path('set-participant/', views.set_participant, name='set_participant'),
    path('idea/', views.idea, name='idea'),
    path('personas/', views.personas, name='personas'),
    path('locations/', views.locations, name='locations'),
    path('scene/', views.scene, name='scene'),
    path('video/', views.video, name='video'),
    path('draft/', views.draft, name='draft'),
    path('reflection/', views.reflection, name='reflection'),
]
