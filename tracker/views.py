"""
Tracker views – satellite tracking, passes, cache, coverage, EO endpoints.
Mirrors all /tracker, /passes, /api/satellites/*, /api/eo-satellites/* routes from Flask app.py.
"""
import json
import logging
from datetime import datetime, timezone, timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.services import get_services

logger = logging.getLogger(__name__)


# ── Page views ───────────────────────────────────────────────────────

def tracker_page(request):
    """GET /tracker"""
    return render(request, 'tracker.html')


def passes_page(request):
    """GET /passes"""
    return render(request, 'passes.html')


def performance_test_page(request):
    """GET /performance-test"""
    return render(request, 'performance-test.html')


# ── Satellite data APIs ──────────────────────────────────────────────

def get_satellites(request):
    """GET /api/satellites"""
    try:
        svc = get_services()
        if len(svc.satellite_manager.satellites) == 0:
            logger.info("Loading TLE data for first time...")
            success = svc.satellite_manager.load_tle_data()
            if not success:
                logger.error("Failed to load satellite data")
                return JsonResponse({
                    'success': False, 'error': 'Failed to load satellite data',
                    'satellites': [], 'satellite_count': 0,
                }, status=500)

        satellites = svc.satellite_manager.get_satellite_data()
        logger.info(f"Retrieved {len(satellites)} satellites")

        return JsonResponse({
            'success': True,
            'satellites': satellites,
            'satellite_count': len(satellites),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'offline_mode': False,
            'cache_status': {
                'has_cache': True,
                'last_update': svc.satellite_manager.last_update.isoformat() if svc.satellite_manager.last_update else None,
                'satellite_count': len(satellites),
            },
        })
    except Exception as e:
        logger.error(f"Error getting satellites: {e}")
        return JsonResponse({
            'success': False, 'error': str(e),
            'satellites': [], 'satellite_count': 0,
        }, status=500)


def get_satellite_details(request, norad_id):
    """GET /api/satellite/<int:norad_id>"""
    try:
        svc = get_services()
        observer_lat = float(request.GET.get('lat', 0))
        observer_lon = float(request.GET.get('lon', 0))
        observer_alt = float(request.GET.get('alt', 0))

        satellite = svc.satellite_manager.get_satellite_by_id(
            norad_id, observer_lat, observer_lon, observer_alt
        )
        if not satellite:
            return JsonResponse({'success': False, 'error': 'Satellite not found'}, status=404)
        return JsonResponse({'success': True, 'satellite': satellite})
    except Exception as e:
        logger.error(f"Error getting satellite {norad_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_categories(request):
    """GET /api/categories"""
    try:
        svc = get_services()
        categories = svc.satellite_manager.get_categories()
        return JsonResponse({'success': True, 'categories': categories})
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return JsonResponse({'success': False, 'error': str(e), 'categories': {}}, status=500)


def search_satellites(request):
    """GET /api/satellites/search"""
    try:
        svc = get_services()
        query = request.GET.get('q', '').strip().lower()
        if not query or len(query) < 2:
            return JsonResponse({'success': True, 'satellites': [], 'query': query})

        satellites = svc.satellite_manager.get_satellite_data()
        matching = [s for s in satellites if query in s['name'].lower()][:50]

        return JsonResponse({
            'success': True, 'satellites': matching,
            'query': query, 'total_matches': len(matching),
        })
    except Exception as e:
        logger.error(f"Error searching satellites: {e}")
        return JsonResponse({'success': False, 'error': str(e), 'satellites': []}, status=500)


@csrf_exempt
@require_POST
def refresh_data(request):
    """POST /api/refresh"""
    try:
        svc = get_services()
        success = svc.satellite_manager.refresh_data()
        if success:
            satellites = svc.satellite_manager.get_satellite_data()
            return JsonResponse({
                'success': True, 'message': 'Data refreshed successfully',
                'satellite_count': len(satellites),
                'timestamp': datetime.now(timezone.utc).isoformat(),
            })
        return JsonResponse({'success': False, 'error': 'Failed to refresh data'}, status=500)
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ── Orbit APIs ───────────────────────────────────────────────────────

def get_satellite_orbit(request, norad_id):
    """GET /api/satellite/<int:norad_id>/orbit"""
    try:
        svc = get_services()
        duration = int(request.GET.get('duration', 3))
        timestamp = request.GET.get('timestamp')

        orbit_points = svc.satellite_manager.get_satellite_orbit(norad_id, duration, timestamp)
        if orbit_points:
            return JsonResponse({
                'success': True, 'orbit_points': orbit_points,
                'duration_hours': duration,
            })
        return JsonResponse({'success': False, 'error': 'Satellite not found or orbit calculation failed'})
    except Exception as e:
        logger.error(f"Error getting orbit for satellite {norad_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


def get_satellite_extended_orbit(request, norad_id):
    """GET /api/satellite/<int:norad_id>/extended-orbit"""
    try:
        svc = get_services()
        days_past = min(max(float(request.GET.get('days_past', 2)), 0.1), 7)
        days_future = min(max(float(request.GET.get('days_future', 2)), 0.1), 7)
        interval_seconds = min(max(int(request.GET.get('interval_seconds', 60)), 10), 300)

        orbit_data = svc.satellite_manager.get_satellite_extended_orbit(
            norad_id, days_past, days_future, interval_seconds
        )
        if orbit_data:
            return JsonResponse({
                'success': True,
                'orbit_points': orbit_data['orbit_points'],
                'current_position_index': orbit_data['current_position_index'],
                'total_points': orbit_data['total_points'],
                'interval_seconds': orbit_data['interval_seconds'],
                'days_past': days_past,
                'days_future': days_future,
            })
        return JsonResponse({'success': False, 'error': 'Satellite not found or extended orbit calculation failed'})
    except Exception as e:
        logger.error(f"Error getting extended orbit for satellite {norad_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


# ── Pass prediction APIs ─────────────────────────────────────────────

def get_satellite_passes(request, norad_id):
    """GET /api/satellite/<int:norad_id>/passes"""
    try:
        svc = get_services()
        lat = float(request.GET.get('lat', 0))
        lon = float(request.GET.get('lon', 0))
        alt = float(request.GET.get('alt', 0))
        time_offset = int(request.GET.get('time_offset', 0))

        passes = svc.satellite_manager.get_satellite_passes(norad_id, lat, lon, int(alt), time_offset)
        fov_info = svc.satellite_manager.eo_satellites.get_satellite_fov(norad_id)
        is_eo = svc.satellite_manager.eo_satellites.is_earth_observation_satellite(norad_id)

        return JsonResponse({
            'success': True, 'passes': passes,
            'is_earth_observation': is_eo, 'fov_info': fov_info,
        })
    except Exception as e:
        logger.error(f"Error getting satellite passes {norad_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_satellite_past_passes(request, norad_id):
    """GET /api/satellite/<int:norad_id>/past-passes"""
    try:
        svc = get_services()
        lat = float(request.GET.get('lat', 0))
        lon = float(request.GET.get('lon', 0))
        alt = float(request.GET.get('alt', 0))
        days_back = int(request.GET.get('days_back', 7))

        past_passes = svc.satellite_manager.get_satellite_past_passes(norad_id, lat, lon, int(alt), days_back)
        satellite_info = svc.satellite_manager.get_satellite_by_id(norad_id)
        fov_info = svc.satellite_manager.eo_satellites.get_satellite_fov(norad_id)
        is_eo = svc.satellite_manager.eo_satellites.is_earth_observation_satellite(norad_id)

        return JsonResponse({
            'success': True, 'past_passes': past_passes,
            'satellite_info': {
                'name': satellite_info['name'] if satellite_info else 'Unknown',
                'norad_id': norad_id,
            },
            'is_earth_observation': is_eo, 'fov_info': fov_info,
            'days_searched': days_back,
        })
    except Exception as e:
        logger.error(f"Error getting past passes for satellite {norad_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_satellites_with_passes_filter(request):
    """GET /api/satellites/passes-filter"""
    try:
        svc = get_services()
        lat = float(request.GET.get('lat', 0))
        lon = float(request.GET.get('lon', 0))
        alt = float(request.GET.get('alt', 0))
        time_filter = request.GET.get('time_filter', '24')

        if not lat and not lon:
            return JsonResponse({
                'success': False, 'error': 'Location coordinates required for pass calculations',
            }, status=400)

        if abs(lat) > 90 or abs(lon) > 180:
            return JsonResponse({
                'success': False, 'error': f'Invalid coordinates: lat={lat}, lon={lon}',
            }, status=400)

        valid_time_filters = ['24', '48', '72', '94', '118', '142']
        if time_filter not in valid_time_filters:
            return JsonResponse({
                'success': False,
                'error': f'Invalid time filter. Must be one of: {", ".join(valid_time_filters)}',
            }, status=400)

        try:
            satellites_with_passes = svc.satellite_manager.get_satellites_with_time_filtered_passes_cached(
                lat, lon, alt, int(time_filter)
            )
            cache_method = "cached_positions"
        except Exception as cache_error:
            logger.warning(f"Cache-based method failed, falling back to traditional: {cache_error}")
            satellites_with_passes = svc.satellite_manager.get_satellites_with_time_filtered_passes(
                lat, lon, alt, int(time_filter)
            )
            cache_method = "traditional_propagation"

        total_satellites = len(svc.satellite_manager.satellites)
        viable_satellites = sum(
            1 for sat in svc.satellite_manager.satellites.values()
            if svc.satellite_manager._is_satellite_viable_for_passes(sat, lat, lon)
        )

        return JsonResponse({
            'success': True,
            'satellites_with_passes': satellites_with_passes,
            'time_filter_hours': int(time_filter),
            'location': {'lat': lat, 'lon': lon, 'alt': alt},
            'calculation_info': {
                'total_satellites': total_satellites,
                'viable_satellites': viable_satellites,
                'cache_method': cache_method,
                'using_position_cache': cache_method == "cached_positions",
            },
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error(f"Error getting satellites with time-filtered passes: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def get_bulk_satellite_passes(request):
    """POST /api/satellites/passes-bulk"""
    try:
        svc = get_services()
        data = json.loads(request.body)
        satellite_ids = data.get('satellite_ids', [])
        lat = float(data.get('lat', 0))
        lon = float(data.get('lon', 0))
        alt = float(data.get('alt', 0))
        time_filter_hours = int(data.get('time_filter_hours', 24))

        if not satellite_ids:
            return JsonResponse({'success': False, 'error': 'No satellite IDs provided'}, status=400)
        if not lat and not lon:
            return JsonResponse({'success': False, 'error': 'Location coordinates required'}, status=400)

        results = svc.satellite_manager.calculate_bulk_passes_cached(
            satellite_ids, lat, lon, alt, time_filter_hours
        )

        valid_results = [r for r in results if r and r.get('passes')]
        valid_results.sort(key=lambda x: x['passes'][0]['rise_time'] if x['passes'] else '9999')
        total_passes = sum(len(r['passes']) for r in valid_results)

        return JsonResponse({
            'success': True,
            'results': valid_results,
            'total_satellites_requested': len(satellite_ids),
            'satellites_with_passes': len(valid_results),
            'total_passes': total_passes,
            'calculation_method': 'cached_positions',
            'location': {'lat': lat, 'lon': lon, 'alt': alt},
            'time_filter_hours': time_filter_hours,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error(f"Error in bulk pass calculation: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def get_cached_passes(request):
    """POST /api/passes/cached"""
    try:
        svc = get_services()
        data = json.loads(request.body)
        if not data:
            return JsonResponse({'success': False, 'error': 'No data provided'}, status=400)

        lat = float(data.get('lat', 0))
        lon = float(data.get('lon', 0))
        alt = float(data.get('alt', 0))
        time_window_hours = int(data.get('time_window_hours', 24))
        min_elevation = float(data.get('min_elevation', 10))

        if abs(lat) > 90 or abs(lon) > 180:
            return JsonResponse({'success': False, 'error': 'Invalid coordinates'}, status=400)

        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=time_window_hours)

        # ULTRA FAST PATH: disk-based spatial-temporal index
        if svc.spatial_index and svc.spatial_index.is_ready():
            passes_found = svc.spatial_index.query_passes(lat, lon, start_time, end_time, min_elevation)

            formatted_passes = []
            for sat_pass in passes_found:
                formatted_passes.append({
                    'norad_id': sat_pass['norad_id'],
                    'name': sat_pass['name'],
                    'category': sat_pass['category'],
                    'color': svc.satellite_manager.satellites.get(sat_pass['norad_id'], {}).get('color', '#64b5f6'),
                    'passes': sat_pass['passes'],
                    'next_pass': sat_pass['passes'][0] if sat_pass['passes'] else None,
                })
            formatted_passes.sort(key=lambda x: x['next_pass']['start'] if x['next_pass'] else '9999')
            total_passes = sum(len(p['passes']) for p in formatted_passes)

            return JsonResponse({
                'success': True, 'passes': formatted_passes,
                'total_satellites_with_passes': len(formatted_passes),
                'total_passes': total_passes,
                'location': {'lat': lat, 'lon': lon, 'alt': alt},
                'time_window_hours': time_window_hours,
                'min_elevation': min_elevation,
                'calculation_method': 'disk_spatial_index',
                'timestamp': datetime.now(timezone.utc).isoformat(),
            })

        # FALLBACK PATH: position cache
        if not svc.position_cache:
            return JsonResponse({
                'success': False,
                'error': 'Position cache not initialized. Please wait for cache to build.',
                'cache_status': 'not_ready',
            }, status=503)

        cache_status = svc.position_cache.get_cache_status()
        stage1_status = cache_status.get('stages', {}).get('stage1', {}).get('status', 'pending')
        if stage1_status != 'completed':
            return JsonResponse({
                'success': False,
                'error': 'Position cache is still building. Please wait 2-5 minutes for Stage 1 to complete.',
                'cache_status': 'building', 'stage1_status': stage1_status,
                'message': 'The cache system is calculating satellite positions. This happens once and takes a few minutes.',
            }, status=503)

        passes_found = []
        satellites_processed = 0
        cache_hits = 0
        for norad_id in list(svc.satellite_manager.satellites.keys()):
            try:
                satellite_passes = svc.position_cache.calculate_pass_predictions_cached_adaptive(
                    norad_id, lat, lon, start_time, end_time, min_elevation
                )
                if satellite_passes:
                    cache_hits += 1
                    sat_data = svc.satellite_manager.satellites.get(norad_id)
                    if sat_data:
                        passes_found.append({
                            'norad_id': norad_id,
                            'name': sat_data['name'],
                            'category': sat_data['category'],
                            'color': sat_data['color'],
                            'passes': satellite_passes,
                            'next_pass': satellite_passes[0] if satellite_passes else None,
                        })
                satellites_processed += 1
            except Exception as e:
                logger.warning(f"Error processing satellite {norad_id}: {e}")

        passes_found.sort(key=lambda x: x['next_pass']['start'] if x['next_pass'] else '9999')
        total_passes = sum(len(p['passes']) for p in passes_found)

        return JsonResponse({
            'success': True, 'passes': passes_found,
            'total_satellites_with_passes': len(passes_found),
            'total_passes': total_passes,
            'location': {'lat': lat, 'lon': lon, 'alt': alt},
            'time_window_hours': time_window_hours,
            'min_elevation': min_elevation,
            'cache_hits': cache_hits,
            'satellites_processed': satellites_processed,
            'calculation_method': 'cached_positions_fallback',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error(f"Error in cached pass prediction: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ── Cache status APIs ────────────────────────────────────────────────

def get_position_cache_status(request):
    """GET /api/position-cache/status"""
    try:
        svc = get_services()
        if svc.position_cache is None:
            return JsonResponse({'success': False, 'error': 'Position cache not initialized'}, status=503)
        st = svc.position_cache.get_cache_status()
        return JsonResponse({'success': True, 'cache_status': st})
    except Exception as e:
        logger.error(f"Error getting position cache status: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_spatial_index_status(request):
    """GET /api/spatial-index/status"""
    try:
        svc = get_services()
        if svc.spatial_index is None:
            return JsonResponse({
                'success': True, 'ready': False, 'status': 'not_initialized',
                'message': 'Spatial index not yet initialized. Building after position cache completes.',
            })
        if not svc.spatial_index.is_ready():
            return JsonResponse({
                'success': True, 'ready': False, 'status': 'building',
                'message': 'Spatial index is currently being built. Please wait...',
            })
        stats = svc.spatial_index.get_stats()
        return JsonResponse({
            'success': True, 'ready': True, 'status': 'ready',
            'stats': stats, 'message': 'Spatial index ready for ultra-fast queries!',
        })
    except Exception as e:
        logger.error(f"Error getting spatial index status: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def create_on_demand_cache(request, norad_id):
    """POST /api/position-cache/on-demand/<int:norad_id>"""
    try:
        svc = get_services()
        if svc.position_cache is None:
            return JsonResponse({'success': False, 'error': 'Position cache not initialized'}, status=503)

        body = json.loads(request.body) if request.body else {}
        duration_hours = min(max(int(body.get('duration_hours', 24)), 1), 168)
        success = svc.position_cache.cache_satellite_on_demand(norad_id, duration_hours)

        if success:
            return JsonResponse({
                'success': True, 'norad_id': norad_id, 'duration_hours': duration_hours,
                'message': f'On-demand cache created for satellite {norad_id} ({duration_hours} hours)',
            })
        return JsonResponse({'success': False, 'error': 'Failed to create on-demand cache'}, status=500)
    except Exception as e:
        logger.error(f"Error creating on-demand cache for satellite {norad_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ── ISS live video ───────────────────────────────────────────────────

def get_iss_live_video(request):
    """GET /api/iss/live-video"""
    try:
        video_info = {
            'video_url': 'https://www.youtube.com/embed/I190Q-ntZbU?autoplay=1&mute=1',
            'backup_urls': [
                'https://www.youtube.com/embed/P9C25Un7xaM?autoplay=1&mute=1',
                'https://www.youtube.com/embed/ddFvjfvPnqk?autoplay=1&mute=1',
                'https://www.youtube.com/embed/4993sBLAzGA?autoplay=1&mute=1',
            ],
            'title': 'ISS Live Video Stream',
            'description': 'Live view from the International Space Station',
            'provider': 'NASA/YouTube',
        }
        return JsonResponse({'success': True, 'video_info': video_info})
    except Exception as e:
        logger.error(f"Error getting ISS live video info: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ── Satellite imagery ────────────────────────────────────────────────

def get_satellite_imagery(request, norad_id, satellite_type):
    """GET /api/satellite/<int:norad_id>/imagery/<satellite_type>"""
    try:
        svc = get_services()
        satellite = svc.satellite_manager.get_satellite_by_id(norad_id)
        if not satellite:
            return JsonResponse({'success': False, 'error': 'Satellite not found'}, status=404)

        imagery_urls = []
        if satellite_type == 'landsat':
            imagery_urls = _get_landsat_imagery(satellite)
        elif satellite_type == 'sentinel':
            imagery_urls = _get_sentinel_imagery(satellite)
        elif satellite_type == 'modis':
            imagery_urls = _get_modis_imagery(satellite)
        elif satellite_type == 'noaa':
            imagery_urls = _get_noaa_imagery(satellite)
        elif satellite_type == 'resurs':
            imagery_urls = _get_resurs_imagery(satellite)

        return JsonResponse({
            'success': True, 'imagery_urls': imagery_urls,
            'satellite_info': {
                'name': satellite['name'],
                'lat': satellite['latitude'],
                'lon': satellite['longitude'],
                'alt': satellite['altitude'],
            },
        })
    except Exception as e:
        logger.error(f"Error getting imagery for satellite {norad_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def _get_landsat_imagery(satellite):
    try:
        return [f"https://landsat-pds.s3.amazonaws.com/c1/L8/sample_image.jpg"]
    except Exception:
        return []


def _get_sentinel_imagery(satellite):
    try:
        return [f"https://scihub.copernicus.eu/dhus/sample_image.jpg"]
    except Exception:
        return []


def _get_modis_imagery(satellite):
    try:
        return [f"https://modis.gsfc.nasa.gov/data/sample_image.jpg"]
    except Exception:
        return []


def _get_noaa_imagery(satellite):
    try:
        return [f"https://cdn.star.nesdis.noaa.gov/GOES16/ABI/FD/GEOCOLOR/latest.jpg"]
    except Exception:
        return []


def _get_resurs_imagery(satellite):
    try:
        return [f"https://gptl.ru/sample_resurs_image.jpg"]
    except Exception:
        return []


# ── Earth Observation satellite coverage ──────────────────────────────

def get_eo_satellites(request):
    """GET /api/eo-satellites"""
    try:
        svc = get_services()
        if not svc.eo_database:
            return JsonResponse({'success': False, 'error': 'EO database not initialized'}, status=503)

        eo_sats = svc.eo_database.get_all_eo_satellites()
        eo_list = []
        for norad_id_str, config in eo_sats.items():
            nid = int(norad_id_str)
            c = config.copy()
            c['norad_id'] = nid
            if nid in svc.satellite_manager.satellites:
                sd = svc.satellite_manager.satellites[nid]
                c['tracked'] = True
                c['current_position'] = {
                    'lat': sd.get('latitude', 0),
                    'lon': sd.get('longitude', 0),
                    'alt': sd.get('altitude', 0),
                }
            else:
                c['tracked'] = False
            eo_list.append(c)

        by_constellation = {}
        for sat in eo_list:
            const = sat.get('constellation', 'Unknown')
            by_constellation.setdefault(const, []).append(sat)

        return JsonResponse({
            'success': True, 'satellites': eo_list,
            'total_count': len(eo_list),
            'by_constellation': by_constellation,
            'constellations': list(by_constellation.keys()),
        })
    except Exception as e:
        logger.error(f"Error getting EO satellites: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_satellite_coverage_swath(request, norad_id):
    """GET /api/satellite/<int:norad_id>/coverage-swath"""
    try:
        svc = get_services()
        if not svc.coverage_calculator:
            return JsonResponse({'success': False, 'error': 'Coverage calculator not initialized'}, status=503)

        hours_past = min(max(float(request.GET.get('hours_past', 1.6)), 0.1), 24)
        hours_future = min(max(float(request.GET.get('hours_future', 1.6)), 0.1), 24)
        interval_minutes = min(max(int(request.GET.get('interval_minutes', 2)), 1), 5)

        coverage_data = svc.coverage_calculator.calculate_coverage_swath(
            norad_id, hours_past, hours_future, interval_minutes
        )
        if not coverage_data:
            return JsonResponse({
                'success': False,
                'error': f'Could not calculate coverage for satellite {norad_id}',
            }, status=404)

        return JsonResponse({
            'success': True, 'coverage': coverage_data,
            'parameters': {
                'hours_past': hours_past,
                'hours_future': hours_future,
                'interval_minutes': interval_minutes,
            },
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error(f"Error calculating coverage swath: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_satellite_ground_swath(request, norad_id):
    """GET /api/satellite/<int:norad_id>/ground-swath"""
    try:
        svc = get_services()
        if not svc.coverage_calculator:
            return JsonResponse({'success': False, 'error': 'Coverage calculator not initialized'}, status=503)

        swath_data = svc.coverage_calculator.calculate_current_ground_swath(norad_id)
        if not swath_data:
            return JsonResponse({
                'success': False,
                'error': f'Could not calculate ground swath for satellite {norad_id}',
            }, status=404)

        return JsonResponse({
            'success': True, 'ground_swath': swath_data,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error(f"Error calculating ground swath: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_satellite_eo_metadata(request, norad_id):
    """GET /api/satellite/<int:norad_id>/eo-metadata"""
    try:
        svc = get_services()
        if not svc.eo_database:
            return JsonResponse({'success': False, 'error': 'EO database not initialized'}, status=503)

        eo_config = svc.eo_database.get_satellite(norad_id)
        if not eo_config:
            return JsonResponse({
                'success': False,
                'error': f'Satellite {norad_id} not found in EO database',
                'is_eo_satellite': False,
            }, status=404)

        if norad_id in svc.satellite_manager.satellites:
            sd = svc.satellite_manager.satellites[norad_id]
            eo_config['current_position'] = {
                'lat': sd.get('latitude', 0),
                'lon': sd.get('longitude', 0),
                'alt': sd.get('altitude', 0),
            }

        return JsonResponse({
            'success': True, 'is_eo_satellite': True,
            'metadata': eo_config, 'norad_id': norad_id,
        })
    except Exception as e:
        logger.error(f"Error getting EO metadata: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_eo_satellites_by_constellation(request, constellation):
    """GET /api/eo-satellites/by-constellation/<constellation>"""
    try:
        svc = get_services()
        if not svc.eo_database:
            return JsonResponse({'success': False, 'error': 'EO database not initialized'}, status=503)
        satellites = svc.eo_database.get_by_constellation(constellation)
        return JsonResponse({
            'success': True, 'constellation': constellation,
            'satellites': satellites, 'count': len(satellites),
        })
    except Exception as e:
        logger.error(f"Error getting satellites by constellation: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_eo_satellites_by_sensor(request, sensor_type):
    """GET /api/eo-satellites/by-sensor/<sensor_type>"""
    try:
        svc = get_services()
        if not svc.eo_database:
            return JsonResponse({'success': False, 'error': 'EO database not initialized'}, status=503)
        satellites = svc.eo_database.get_by_sensor_type(sensor_type)
        return JsonResponse({
            'success': True, 'sensor_type': sensor_type,
            'satellites': satellites, 'count': len(satellites),
        })
    except Exception as e:
        logger.error(f"Error getting satellites by sensor type: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ── SAR Pass Prediction Pipeline ─────────────────────────────────────

@csrf_exempt
def sar_passes(request):
    """
    POST /api/sar-passes
    ─────────────────────
    Accepts a JSON body with the parsed NLU intent (or raw query + coords)
    and returns ranked SAR satellite pass predictions.

    Request body (all optional except location OR lat+lon):
      {
        "query"        : "which SAR passes over London next 24h",  // raw text
        "lat"          : 51.5,          // explicit lat (overrides query)
        "lon"          : -0.12,         // explicit lon (overrides query)
        "time_hours"   : 48,            // prediction window hours (default 48)
        "band_filter"  : "C",           // optional: C/X/L/S
        "agency_filter": "ESA",         // optional
        "min_elevation": 10,            // degrees (default 10)
        "max_results"  : 10,            // default 10
      }

    Response:
      {
        "success"    : true,
        "passes"     : [ {...pass_record...}, ... ],
        "total_found": int,
        "satellites_checked": int,
        "location"   : {"name", "lat", "lon"},
        "time_hours" : float,
        "filters"    : { "band", "agency" },
        "intent"     : { ...nlu_fields... },
      }
    """
    try:
        import json as _json
        from core.sar_nlu import extract_sar_intent
        from tracker.sar_pass_predictor import predict_sar_passes

        # ── Parse request ──────────────────────────────────────────────
        if request.method not in ("GET", "POST"):
            return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

        if request.method == "POST":
            try:
                body = _json.loads(request.body)
            except Exception:
                body = {}
        else:
            body = {}

        query     = body.get("query", "SAR pass prediction")
        lat_param = body.get("lat")
        lon_param = body.get("lon")

        # Run NLU on the query; then override with explicit params
        intent = extract_sar_intent(
            query,
            browser_lat=float(lat_param) if lat_param is not None else None,
            browser_lon=float(lon_param) if lon_param is not None else None,
        )

        # Allow direct parameter overrides (UI sends explicit lat/lon)
        if lat_param is not None and lon_param is not None:
            intent["location"] = {
                "name": body.get("location_name", f"{float(lat_param):.4f}°, {float(lon_param):.4f}°"),
                "lat": float(lat_param),
                "lon": float(lon_param),
            }

        if "time_hours" in body:
            intent["time_hours"] = min(float(body["time_hours"]), 168.0)

        if "band_filter" in body and body["band_filter"]:
            intent["band_filter"] = str(body["band_filter"]).upper()

        if "agency_filter" in body and body["agency_filter"]:
            intent["agency_filter"] = str(body["agency_filter"])

        if "min_elevation" in body:
            intent["min_elevation"] = float(body["min_elevation"])

        max_results = int(body.get("max_results", 10))
        max_results = max(10, min(50, max_results))    # enforce 10–50 range

        # ── Run prediction pipeline ────────────────────────────────────
        svc = get_services()
        if not svc.satellite_manager or len(svc.satellite_manager.satellites) == 0:
            svc.satellite_manager.load_tle_data()

        result = predict_sar_passes(svc.satellite_manager, intent, max_results=max_results)

        return JsonResponse({
            "success":             True,
            "passes":              result["passes"],
            "total_found":         result["total_found"],
            "satellites_checked":  result["satellites_checked"],
            "location":            result["location"],
            "time_hours":          result["time_hours"],
            "filters":             result["filters"],
            "intent":              {k: v for k, v in intent.items() if k != "sar_info"},
        })

    except Exception as e:
        logger.error(f"SAR pass prediction error: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def sar_satellite_list(request):
    """
    GET /api/sar-satellites
    Returns the full SAR satellite database (metadata only, no TLE).
    Useful for the UI to populate filter dropdowns.
    """
    try:
        from tracker.sar_satellite_db import SAR_SATELLITES
        satellites = []
        for norad_id, info in SAR_SATELLITES.items():
            satellites.append({
                "norad_id":     norad_id,
                "name":         info["name"],
                "constellation":info["constellation"],
                "agency":       info["agency"],
                "country":      info["country"],
                "band":         info["band"],
                "frequency_ghz":info["frequency_ghz"],
                "wavelength_cm":info["wavelength_cm"],
                "default_mode": info["default_mode"],
                "repeat_cycle_days": info["repeat_cycle_days"],
                "altitude_km":  info["altitude_km"],
                "status":       info["status"],
                "launch_date":  info["launch_date"],
                "use_cases":    info["use_cases"],
                "color":        info.get("color", "#00b4d8"),
                "icon":         info.get("icon", "📡"),
            })
        return JsonResponse({"success": True, "satellites": satellites, "count": len(satellites)})
    except Exception as e:
        logger.error(f"SAR satellite list error: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ── Universal EO Pass Prediction Pipeline ────────────────────────────

@csrf_exempt
def eo_passes(request):
    """
    POST /api/eo-passes
    ───────────────────
    Universal EO satellite pass endpoint. Handles any sensor type, specific
    satellite name, constellation query, or use-case goal.

    Request body (JSON):
      {
        "query"          : "optical satellites over London next 24h",  // raw NLU text
        "lat"            : 51.5,           // explicit lat (overrides query location)
        "lon"            : -0.12,          // explicit lon
        "sensor_type"    : "optical",      // optional override
        "satellite_name" : "LANDSAT-9",    // optional
        "constellation"  : "Planet Labs",  // optional
        "time_hours"     : 48,             // default 48
        "use_case"       : "flood",        // optional
        "min_elevation"  : 10,             // degrees, default 10
        "max_results"    : 15,             // default 15
        "daylight_only"  : false           // optional, auto-set for optical
      }

    Returns:
      {
        "success"             : true,
        "passes"              : [...],
        "total_found"         : int,
        "satellites_checked"  : int,
        "location"            : {...},
        "time_hours"          : float,
        "filters"             : {...},
        "intent_summary"      : "...",
      }
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        import json as _json
        body = _json.loads(request.body or b"{}")

        # ── Build intent from query text + optional explicit fields ───────
        from core.eo_pass_nlu import extract_eo_pass_intent, describe_eo_intent
        query = body.get("query", "")
        raw_lat = body.get("lat")
        raw_lon = body.get("lon")
        blat = float(raw_lat) if raw_lat is not None else None
        blon = float(raw_lon) if raw_lon is not None else None

        intent = extract_eo_pass_intent(query, browser_lat=blat, browser_lon=blon)

        # Allow explicit field overrides (REST-style call without NLU text)
        if body.get("sensor_type"):
            intent["sensor_type"] = body["sensor_type"]
            intent["is_eo_pass_query"] = True
        if body.get("satellite_name"):
            intent["specific_satellite"] = body["satellite_name"]
            intent["is_eo_pass_query"] = True
        if body.get("constellation"):
            intent["constellation"] = body["constellation"]
            intent["is_eo_pass_query"] = True
        if body.get("use_case"):
            intent["use_case"] = body["use_case"]
            intent["is_eo_pass_query"] = True
        if body.get("time_hours"):
            intent["time_hours"] = float(body["time_hours"])
        if body.get("min_elevation") is not None:
            intent["min_elevation"] = float(body["min_elevation"])
        if body.get("daylight_only") is not None:
            intent["daylight_only"] = bool(body["daylight_only"])
        if body.get("resolution_tier"):
            intent["resolution_tier"] = body["resolution_tier"]

        # Inject explicit lat/lon into location if present
        if blat is not None and blon is not None:
            if not intent.get("location"):
                intent["location"] = {"name": "Specified location", "lat": blat, "lon": blon}
            intent["use_browser_location"] = False

        if not intent.get("is_eo_pass_query"):
            # Accept even without NLU trigger when called via REST
            if any([intent.get("sensor_type"), intent.get("specific_satellite"),
                    intent.get("constellation"), intent.get("location")]):
                intent["is_eo_pass_query"] = True

        max_results = int(body.get("max_results", 15))
        max_results = max(5, min(50, max_results))

        # ── Run the pipeline ──────────────────────────────────────────────
        svc = get_services()
        if not svc.satellite_manager or len(svc.satellite_manager.satellites) == 0:
            svc.satellite_manager.load_tle_data()

        # Use cached FOV database from services singleton
        fov_db = svc.fov_db
        if fov_db is None:
            from tracker.satellite_fov_data import EarthObservationSatellites
            fov_db = EarthObservationSatellites()

        from tracker.eo_satellite_resolver import resolve_satellites
        from tracker.eo_pass_predictor import predict_eo_passes

        candidates = resolve_satellites(
            intent,
            svc.satellite_manager,
            fov_db,
            svc.eo_database,
        )

        result = predict_eo_passes(
            intent=intent,
            candidates=candidates,
            satellite_manager=svc.satellite_manager,
            fov_db=fov_db,
            spatial_index=svc.spatial_index,
            max_results=max_results,
        )

        return JsonResponse({
            "success":            True,
            "passes":             result["passes"],
            "total_found":        result["total_found"],
            "satellites_checked": result["satellites_checked"],
            "location":           result["location"],
            "time_hours":         result["time_hours"],
            "filters":            result["filters"],
            "intent_summary":     describe_eo_intent(intent),
            "error":              result.get("error"),
        })

    except Exception as e:
        logger.error(f"EO pass prediction error: {e}", exc_info=True)
        return JsonResponse({"success": False, "error": str(e)}, status=500)
