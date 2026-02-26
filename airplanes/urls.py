from django.urls import path
from airplanes import views

urlpatterns = [
    path('api/airplanes', views.get_airplanes, name='get_airplanes'),
    path('api/airplane/<str:icao24>', views.get_airplane_details, name='get_airplane_details'),
]
