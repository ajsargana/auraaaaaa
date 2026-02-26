# Sat-Track Django Project Structure

> **Converted from Flask → Django**
> All original Python logic is preserved unchanged. Only the routing layer (Flask `@app.route` → Django views) was rewritten.

## Directory Tree

```
E:\Sat-Track_latest\
├── manage.py
├── sat_track/                  # Django project config
│   ├── settings.py             # Apps, middleware, paths
│   ├── urls.py                 # Root URL conf → includes all 5 apps
│   └── wsgi.py
│
├── core/                       # Landing, chat, status, shared init
│   ├── views.py                # 8 views
│   ├── urls.py
│   ├── services.py             # AppServices singleton (replaces app.py init)
│   ├── middleware.py            # CORS middleware
│   ├── ai_chat_module.py       # ← copied from source
│   ├── data/                   # ← copied data files
│   │   ├── space_facts.txt
│   │   ├── satellite_facts.txt
│   │   ├── eo_satellites.json
│   │   └── de421.bsp
│   └── templates/              # HTML templates go here
│
├── tracker/                    # Satellite tracking, passes, cache, EO
│   ├── views.py                # 30+ views
│   ├── urls.py
│   ├── satellite_data_simple.py
│   ├── satellite_categories.py
│   ├── satellite_fov_data.py
│   ├── satellite_coverage_3d.py
│   ├── satellite_coverage_eopredictor.py
│   ├── eo_satellite_database.py
│   ├── initialize_eo_system.py
│   ├── position_cache_manager_optimized.py
│   ├── sliding_window_cache.py
│   ├── smart_cache_manager.py
│   ├── spatial_index_disk.py
│   ├── spatial_temporal_index.py
│   ├── tle_updater.py
│   ├── rebuild_cache.py
│   ├── rebuild_sliding_cache.py
│   └── rebuild_spatial_index.py
│
├── nasa/                       # NASA APOD, Asteroids, DONKI, EONET
│   ├── views.py                # 12 views
│   ├── urls.py
│   ├── nasa_apod_module.py
│   ├── nasa_asteroids_module.py
│   ├── donki_module.py
│   └── nasa_eonet_module.py
│
├── launches/                   # Rocket launches
│   ├── views.py                # 3 views
│   ├── urls.py
│   └── launch_data_module.py
│
├── airplanes/                  # Airplane tracking
│   ├── views.py                # 2 views
│   ├── urls.py
│   └── airplane_data.py
│
└── source/                     # Original Flask source (reference only)
```

---

## Flask Route → Django View Mapping

### Core App (`core/views.py`)

| Flask Route | Method | Flask Function | Django View | Django URL Name |
|---|---|---|---|---|
| `/` | GET | `landing()` | `core.views.landing` | `landing` |
| `/test` | GET | — | `core.views.test_view` | `test` |
| `/api/random-space-fact` | GET | `random_space_fact()` | `core.views.random_space_fact` | `random_space_fact` |
| `/api/random-satellite-fact` | GET | `random_satellite_fact()` | `core.views.random_satellite_fact` | `random_satellite_fact` |
| `/api/chat` | POST | `chat()` | `core.views.chat` | `chat` |
| `/api/status` | GET | `status()` | `core.views.status` | `status` |
| `/api/weather-key` | GET | `get_weather_key()` | `core.views.weather_key` | `weather_key` |
| `/api/user/preferences` | GET/POST | `user_preferences()` | `core.views.user_preferences` | `user_preferences` |

### Tracker App (`tracker/views.py`)

| Flask Route | Method | Flask Function | Django View | Django URL Name |
|---|---|---|---|---|
| `/tracker` | GET | `tracker()` | `tracker.views.tracker_page` | `tracker` |
| `/passes` | GET | `passes()` | `tracker.views.passes_page` | `passes` |
| `/performance-test` | GET | `performance_test()` | `tracker.views.performance_test_page` | `performance_test` |
| `/api/satellites` | GET | `get_satellites()` | `tracker.views.get_satellites` | `get_satellites` |
| `/api/satellite/<id>` | GET | `get_satellite_details()` | `tracker.views.get_satellite_details` | `get_satellite_details` |
| `/api/categories` | GET | `get_categories()` | `tracker.views.get_categories` | `get_categories` |
| `/api/satellites/search` | GET | `search_satellites()` | `tracker.views.search_satellites` | `search_satellites` |
| `/api/refresh` | POST | `refresh_data()` | `tracker.views.refresh_data` | `refresh_data` |
| `/api/satellite/<id>/orbit` | GET | `get_satellite_orbit()` | `tracker.views.get_satellite_orbit` | `get_satellite_orbit` |
| `/api/satellite/<id>/extended-orbit` | GET | `get_satellite_extended_orbit()` | `tracker.views.get_satellite_extended_orbit` | `get_satellite_extended_orbit` |
| `/api/satellite/<id>/passes` | GET | `get_satellite_passes()` | `tracker.views.get_satellite_passes` | `get_satellite_passes` |
| `/api/satellite/<id>/past-passes` | GET | `get_satellite_past_passes()` | `tracker.views.get_satellite_past_passes` | `get_satellite_past_passes` |
| `/api/satellites/passes-filter` | GET | `get_satellites_with_passes_filter()` | `tracker.views.get_satellites_with_passes_filter` | `get_satellites_with_passes_filter` |
| `/api/satellites/passes-bulk` | POST | `get_bulk_satellite_passes()` | `tracker.views.get_bulk_satellite_passes` | `get_bulk_satellite_passes` |
| `/api/passes/cached` | POST | `get_cached_passes()` | `tracker.views.get_cached_passes` | `get_cached_passes` |
| `/api/position-cache/status` | GET | `get_position_cache_status()` | `tracker.views.get_position_cache_status` | `get_position_cache_status` |
| `/api/spatial-index/status` | GET | `get_spatial_index_status()` | `tracker.views.get_spatial_index_status` | `get_spatial_index_status` |
| `/api/position-cache/on-demand/<id>` | POST | `create_on_demand_cache()` | `tracker.views.create_on_demand_cache` | `create_on_demand_cache` |
| `/api/iss/live-video` | GET | `get_iss_live_video()` | `tracker.views.get_iss_live_video` | `get_iss_live_video` |
| `/api/satellite/<id>/imagery/<type>` | GET | `get_satellite_imagery()` | `tracker.views.get_satellite_imagery` | `get_satellite_imagery` |
| `/api/eo-satellites` | GET | `get_eo_satellites()` | `tracker.views.get_eo_satellites` | `get_eo_satellites` |
| `/api/satellite/<id>/coverage-swath` | GET | `get_satellite_coverage_swath()` | `tracker.views.get_satellite_coverage_swath` | `get_satellite_coverage_swath` |
| `/api/satellite/<id>/ground-swath` | GET | `get_satellite_ground_swath()` | `tracker.views.get_satellite_ground_swath` | `get_satellite_ground_swath` |
| `/api/satellite/<id>/eo-metadata` | GET | `get_satellite_eo_metadata()` | `tracker.views.get_satellite_eo_metadata` | `get_satellite_eo_metadata` |
| `/api/eo-satellites/by-constellation/<c>` | GET | `get_eo_satellites_by_constellation()` | `tracker.views.get_eo_satellites_by_constellation` | `get_eo_satellites_by_constellation` |
| `/api/eo-satellites/by-sensor/<type>` | GET | `get_eo_satellites_by_sensor()` | `tracker.views.get_eo_satellites_by_sensor` | `get_eo_satellites_by_sensor` |

### NASA App (`nasa/views.py`)

| Flask Route | Method | Flask Function | Django View | Django URL Name |
|---|---|---|---|---|
| `/nasa-picture-of-the-day` | GET | `nasa_apod_page()` | `nasa.views.nasa_apod_page` | `nasa_apod_page` |
| `/nasa-asteroids` | GET | `nasa_asteroids_page()` | `nasa.views.nasa_asteroids_page` | `nasa_asteroids_page` |
| `/nasa-space-weather` | GET | `nasa_space_weather_page()` | `nasa.views.nasa_space_weather_page` | `nasa_space_weather_page` |
| `/nasa-eonet` | GET | `nasa_eonet_page()` | `nasa.views.nasa_eonet_page` | `nasa_eonet_page` |
| `/api/nasa/apod` | GET | `get_nasa_apod()` | `nasa.views.get_nasa_apod` | `get_nasa_apod` |
| `/api/nasa/apod/recent` | GET | `get_recent_nasa_apods()` | `nasa.views.get_recent_nasa_apods` | `get_recent_nasa_apods` |
| `/api/nasa/apod/download` | GET | `download_nasa_image()` | `nasa.views.download_nasa_image` | `download_nasa_image` |
| `/api/nasa/asteroids` | GET | `get_nasa_asteroids()` | `nasa.views.get_nasa_asteroids` | `get_nasa_asteroids` |
| `/api/nasa/asteroids/<id>` | GET | `get_nasa_asteroid_details()` | `nasa.views.get_nasa_asteroid_details` | `get_nasa_asteroid_details` |
| `/api/nasa/donki/space-weather` | GET | `get_nasa_space_weather()` | `nasa.views.get_nasa_space_weather` | `get_nasa_space_weather` |
| `/api/nasa/eonet/events` | GET | `get_nasa_eonet_events()` | `nasa.views.get_nasa_eonet_events` | `get_nasa_eonet_events` |
| `/api/nasa/eonet/events/<id>` | GET | `get_nasa_eonet_event_details()` | `nasa.views.get_nasa_eonet_event_details` | `get_nasa_eonet_event_details` |
| `/api/nasa/eonet/events/category/<id>` | GET | `get_nasa_eonet_events_by_category()` | `nasa.views.get_nasa_eonet_events_by_category` | `get_nasa_eonet_events_by_category` |

### Launches App (`launches/views.py`)

| Flask Route | Method | Flask Function | Django View | Django URL Name |
|---|---|---|---|---|
| `/launches` | GET | `launches_page()` | `launches.views.launches_page` | `launches_page` |
| `/api/launches/upcoming` | GET | `get_upcoming_launches()` | `launches.views.get_upcoming_launches` | `get_upcoming_launches` |
| `/api/launches/analytics` | GET | `get_launch_analytics()` | `launches.views.get_launch_analytics` | `get_launch_analytics` |

### Airplanes App (`airplanes/views.py`)

| Flask Route | Method | Flask Function | Django View | Django URL Name |
|---|---|---|---|---|
| `/api/airplanes` | GET | `get_airplanes()` | `airplanes.views.get_airplanes` | `get_airplanes` |
| `/api/airplane/<icao24>` | GET | `get_airplane_details()` | `airplanes.views.get_airplane_details` | `get_airplane_details` |

---

## Key Architecture Decisions

| Concern | Flask (before) | Django (after) |
|---|---|---|
| **Routing** | `@app.route()` decorators in `app.py` | `urls.py` per app + root `sat_track/urls.py` |
| **JSON responses** | `flask.jsonify()` | `django.http.JsonResponse()` |
| **Template rendering** | `flask.render_template()` | `django.shortcuts.render()` |
| **Request data** | `flask.request.args` / `request.json` | `request.GET` / `json.loads(request.body)` |
| **CORS** | `@app.after_request` | `core.middleware.CorsMiddleware` |
| **CSRF** | Not applicable | `@csrf_exempt` on POST API views |
| **Init / startup** | Module-level code in `app.py` | `core.services.AppServices` singleton |
| **Support modules** | All in one directory | Copied to their respective app directories |

## Running the Project

```bash
# Activate virtualenv
.\venv\Scripts\activate

# Run Django check
python manage.py check

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```
