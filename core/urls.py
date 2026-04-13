from django.urls import path
from core import views

urlpatterns = [
    # Pages
    path('', views.landing, name='landing'),
    path('test', views.test_view, name='test'),

    # APIs
    path('api/random-space-fact', views.random_space_fact, name='random_space_fact'),
    path('api/random-satellite-fact', views.random_satellite_fact, name='random_satellite_fact'),
    path('api/chat', views.chat, name='chat'),
    path('api/status', views.status, name='status'),
    path('api/weather-key', views.weather_key, name='weather_key'),
    path('api/user/preferences', views.user_preferences, name='user_preferences'),

    # Tile cache proxy — serves cached tiles, fetches from upstream on miss
    path('tiles/<str:provider>/<int:z>/<int:x>/<int:y>/', views.tile_proxy, name='tile_proxy'),
]
