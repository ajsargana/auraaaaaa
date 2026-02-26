from django.urls import path
from tracker import views

urlpatterns = [
    # Pages
    path('tracker', views.tracker_page, name='tracker'),
    path('passes', views.passes_page, name='passes'),
    path('performance-test', views.performance_test_page, name='performance_test'),

    # Satellite data
    path('api/satellites', views.get_satellites, name='get_satellites'),
    path('api/satellite/<int:norad_id>', views.get_satellite_details, name='get_satellite_details'),
    path('api/categories', views.get_categories, name='get_categories'),
    path('api/satellites/search', views.search_satellites, name='search_satellites'),
    path('api/refresh', views.refresh_data, name='refresh_data'),

    # Orbits
    path('api/satellite/<int:norad_id>/orbit', views.get_satellite_orbit, name='get_satellite_orbit'),
    path('api/satellite/<int:norad_id>/extended-orbit', views.get_satellite_extended_orbit, name='get_satellite_extended_orbit'),

    # Passes
    path('api/satellite/<int:norad_id>/passes', views.get_satellite_passes, name='get_satellite_passes'),
    path('api/satellite/<int:norad_id>/past-passes', views.get_satellite_past_passes, name='get_satellite_past_passes'),
    path('api/satellites/passes-filter', views.get_satellites_with_passes_filter, name='get_satellites_with_passes_filter'),
    path('api/satellites/passes-bulk', views.get_bulk_satellite_passes, name='get_bulk_satellite_passes'),
    path('api/passes/cached', views.get_cached_passes, name='get_cached_passes'),

    # Cache
    path('api/position-cache/status', views.get_position_cache_status, name='get_position_cache_status'),
    path('api/spatial-index/status', views.get_spatial_index_status, name='get_spatial_index_status'),
    path('api/position-cache/on-demand/<int:norad_id>', views.create_on_demand_cache, name='create_on_demand_cache'),

    # ISS
    path('api/iss/live-video', views.get_iss_live_video, name='get_iss_live_video'),

    # Imagery
    path('api/satellite/<int:norad_id>/imagery/<str:satellite_type>', views.get_satellite_imagery, name='get_satellite_imagery'),

    # Earth Observation
    path('api/eo-satellites', views.get_eo_satellites, name='get_eo_satellites'),
    path('api/satellite/<int:norad_id>/coverage-swath', views.get_satellite_coverage_swath, name='get_satellite_coverage_swath'),
    path('api/satellite/<int:norad_id>/ground-swath', views.get_satellite_ground_swath, name='get_satellite_ground_swath'),
    path('api/satellite/<int:norad_id>/eo-metadata', views.get_satellite_eo_metadata, name='get_satellite_eo_metadata'),
    path('api/eo-satellites/by-constellation/<str:constellation>', views.get_eo_satellites_by_constellation, name='get_eo_satellites_by_constellation'),
    path('api/eo-satellites/by-sensor/<str:sensor_type>', views.get_eo_satellites_by_sensor, name='get_eo_satellites_by_sensor'),

    # SAR Pass Prediction Pipeline
    path('api/sar-passes', views.sar_passes, name='sar_passes'),
    path('api/sar-satellites', views.sar_satellite_list, name='sar_satellite_list'),

    # Universal EO Pass Prediction Pipeline
    path('api/eo-passes', views.eo_passes, name='eo_passes'),
]
