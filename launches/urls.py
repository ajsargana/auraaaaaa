from django.urls import path
from launches import views

urlpatterns = [
    path('launches', views.launches_page, name='launches_page'),
    path('api/launches/upcoming', views.get_upcoming_launches, name='get_upcoming_launches'),
    path('api/launches/analytics', views.get_launch_analytics, name='get_launch_analytics'),
]
