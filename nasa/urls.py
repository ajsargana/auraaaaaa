from django.urls import path
from nasa import views

urlpatterns = [
    # Pages
    path('nasa-picture-of-the-day', views.nasa_apod_page, name='nasa_apod_page'),
    path('nasa-asteroids', views.nasa_asteroids_page, name='nasa_asteroids_page'),
    path('nasa-space-weather', views.nasa_space_weather_page, name='nasa_space_weather_page'),
    path('nasa-eonet', views.nasa_eonet_page, name='nasa_eonet_page'),

    # APOD APIs
    path('api/nasa/apod', views.get_nasa_apod, name='get_nasa_apod'),
    path('api/nasa/apod/recent', views.get_recent_nasa_apods, name='get_recent_nasa_apods'),
    path('api/nasa/apod/download', views.download_nasa_image, name='download_nasa_image'),

    # Asteroids APIs
    path('api/nasa/asteroids', views.get_nasa_asteroids, name='get_nasa_asteroids'),
    path('api/nasa/asteroids/<str:asteroid_id>', views.get_nasa_asteroid_details, name='get_nasa_asteroid_details'),

    # DONKI Space Weather API
    path('api/nasa/donki/space-weather', views.get_nasa_space_weather, name='get_nasa_space_weather'),

    # EONET Events APIs
    path('api/nasa/eonet/events', views.get_nasa_eonet_events, name='get_nasa_eonet_events'),
    path('api/nasa/eonet/events/category/<str:category_id>', views.get_nasa_eonet_events_by_category, name='get_nasa_eonet_events_by_category'),
    path('api/nasa/eonet/events/<str:event_id>', views.get_nasa_eonet_event_details, name='get_nasa_eonet_event_details'),
]
