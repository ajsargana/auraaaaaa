"""
NASA views — APOD, Asteroids, DONKI Space Weather, EONET Natural Events.
Mirrors all /nasa-*, /api/nasa/* routes from the original Flask app.py.
"""
import logging
import requests
from datetime import datetime, timezone

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from core.services import get_services

logger = logging.getLogger(__name__)


# ── Page views ───────────────────────────────────────────────────────

def nasa_apod_page(request):
    """GET /nasa-picture-of-the-day"""
    return render(request, 'nasa_apod.html')


def nasa_asteroids_page(request):
    """GET /nasa-asteroids"""
    return render(request, 'nasa_asteroids.html')


def nasa_space_weather_page(request):
    """GET /nasa-space-weather"""
    return render(request, 'nasa_space_weather.html')


def nasa_eonet_page(request):
    """GET /nasa-eonet"""
    return render(request, 'nasa_eonet.html')


# ── APOD APIs ────────────────────────────────────────────────────────

def get_nasa_apod(request):
    """GET /api/nasa/apod"""
    try:
        svc = get_services()
        date = request.GET.get('date')
        apod_data = svc.nasa_apod_module.get_picture_of_the_day(date)
        return JsonResponse(apod_data)
    except Exception as e:
        logger.error(f"Error getting NASA APOD: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_recent_nasa_apods(request):
    """GET /api/nasa/apod/recent"""
    try:
        svc = get_services()
        count = int(request.GET.get('count', 5))
        recent_data = svc.nasa_apod_module.get_recent_pictures(count)
        return JsonResponse(recent_data)
    except Exception as e:
        logger.error(f"Error getting recent NASA APODs: {e}")
        return JsonResponse({
            'success': False, 'error': str(e),
            'pictures': [], 'count': 0,
        }, status=500)


def download_nasa_image(request):
    """GET /api/nasa/apod/download"""
    try:
        svc = get_services()
        image_type = request.GET.get('type', 'hd')
        filename = request.GET.get('filename', 'nasa_image.jpg')
        date = request.GET.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))

        cached_data = svc.nasa_apod_module._get_from_cache(date)
        if not cached_data or not cached_data.get('success'):
            return JsonResponse({'success': False, 'error': 'No cached image data found'}, status=404)

        if image_type == 'hd' and cached_data.get('hdurl'):
            image_url = cached_data['hdurl']
        else:
            image_url = cached_data.get('url')

        if not image_url:
            return JsonResponse({'success': False, 'error': 'No image URL found in cache'}, status=404)

        resp = requests.get(image_url, timeout=30)
        resp.raise_for_status()
        content_type = resp.headers.get('content-type', 'image/jpeg')

        response = HttpResponse(resp.content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = str(len(resp.content))
        return response
    except requests.RequestException as e:
        logger.error(f"Error downloading NASA image: {e}")
        return JsonResponse({'success': False, 'error': f'Failed to download image: {str(e)}'}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error downloading NASA image: {e}")
        return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'}, status=500)


# ── Asteroids APIs ───────────────────────────────────────────────────

def get_nasa_asteroids(request):
    """GET /api/nasa/asteroids"""
    try:
        svc = get_services()
        if not svc.nasa_asteroids_module:
            return JsonResponse({
                'success': False, 'error': 'NASA Asteroids module not initialized',
                'asteroids': [], 'total_count': 0,
            }, status=500)
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        asteroids_data = svc.nasa_asteroids_module.get_near_earth_asteroids(start_date, end_date)
        return JsonResponse(asteroids_data)
    except Exception as e:
        logger.error(f"Error getting NASA Asteroids: {e}")
        return JsonResponse({
            'success': False, 'error': str(e),
            'asteroids': [], 'total_count': 0,
        }, status=500)


def get_nasa_asteroid_details(request, asteroid_id):
    """GET /api/nasa/asteroids/<asteroid_id>"""
    try:
        svc = get_services()
        if not svc.nasa_asteroids_module:
            return JsonResponse({'success': False, 'error': 'NASA Asteroids module not initialized'}, status=500)
        if not asteroid_id or not asteroid_id.strip():
            return JsonResponse({'success': False, 'error': 'Invalid asteroid ID provided'}, status=400)
        details = svc.nasa_asteroids_module.get_asteroid_details(asteroid_id.strip())
        if not details:
            return JsonResponse({
                'success': False, 'error': f'No details found for asteroid {asteroid_id}',
            }, status=404)
        return JsonResponse(details)
    except Exception as e:
        logger.error(f"Error getting asteroid details {asteroid_id}: {e}")
        return JsonResponse({
            'success': False, 'error': f'Failed to fetch asteroid details: {str(e)}',
        }, status=500)


# ── DONKI Space Weather APIs ─────────────────────────────────────────

def get_nasa_space_weather(request):
    """GET /api/nasa/donki/space-weather"""
    try:
        svc = get_services()
        if not svc.nasa_donki_module:
            return JsonResponse({
                'success': False, 'error': 'NASA DONKI module not initialized',
                'space_weather': {},
            }, status=500)
        data = svc.nasa_donki_module.get_space_weather_data()
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error getting NASA space weather: {e}")
        return JsonResponse({
            'success': False, 'error': str(e), 'space_weather': {},
        }, status=500)


# ── EONET Events APIs ────────────────────────────────────────────────

def get_nasa_eonet_events(request):
    """GET /api/nasa/eonet/events"""
    try:
        svc = get_services()
        if not svc.nasa_eonet_module:
            return JsonResponse({
                'success': False, 'error': 'NASA EONET module not initialized',
                'events': [], 'categories': {}, 'total_count': 0,
            }, status=500)
        data = svc.nasa_eonet_module.get_natural_events()
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error getting NASA EONET events: {e}")
        return JsonResponse({
            'success': False, 'error': str(e),
            'events': [], 'categories': {}, 'total_count': 0,
        }, status=500)


def get_nasa_eonet_event_details(request, event_id):
    """GET /api/nasa/eonet/events/<event_id>"""
    try:
        svc = get_services()
        if not svc.nasa_eonet_module:
            return JsonResponse({'success': False, 'error': 'NASA EONET module not initialized'}, status=500)
        if not event_id or not event_id.strip():
            return JsonResponse({'success': False, 'error': 'Invalid event ID provided'}, status=400)
        details = svc.nasa_eonet_module.get_event_details(event_id.strip())
        if not details:
            return JsonResponse({
                'success': False, 'error': f'No details found for event {event_id}',
            }, status=404)
        return JsonResponse(details)
    except Exception as e:
        logger.error(f"Error getting EONET event details {event_id}: {e}")
        return JsonResponse({
            'success': False, 'error': f'Failed to fetch event details: {str(e)}',
        }, status=500)


def get_nasa_eonet_events_by_category(request, category_id):
    """GET /api/nasa/eonet/events/category/<category_id>"""
    try:
        svc = get_services()
        if not svc.nasa_eonet_module:
            return JsonResponse({'success': False, 'error': 'NASA EONET module not initialized'}, status=500)
        data = svc.nasa_eonet_module.get_events_by_category(category_id)
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error getting EONET events by category: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
