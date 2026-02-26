"""
Airplanes views — airplane tracking endpoints.
Mirrors /api/airplanes, /api/airplane/* routes from the original Flask app.py.
"""
import logging
from datetime import datetime, timezone

from django.http import JsonResponse

from core.services import get_services

logger = logging.getLogger(__name__)


def get_airplanes(request):
    """GET /api/airplanes"""
    try:
        svc = get_services()
        force_refresh = request.GET.get('force_refresh', 'false').lower() == 'true'
        success = svc.airplane_manager.load_airplane_data(force_refresh=force_refresh)

        if success:
            airplanes = svc.airplane_manager.get_airplane_data()

            is_cached = (
                svc.airplane_manager.last_api_call
                and (datetime.now(timezone.utc) - svc.airplane_manager.last_api_call).total_seconds() > 5
            )

            return JsonResponse({
                'success': True,
                'airplanes': airplanes,
                'airplane_count': len(airplanes),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'OpenSky Network',
                'cached': is_cached,
                'last_api_call': svc.airplane_manager.last_api_call.isoformat() if svc.airplane_manager.last_api_call else None,
                'processing_stats': {'final_count': len(airplanes)},
            })
        return JsonResponse({
            'success': False, 'error': 'Failed to load airplane data',
            'airplanes': [], 'airplane_count': 0,
        }, status=500)
    except Exception as e:
        logger.error(f"Error getting airplanes: {e}")
        return JsonResponse({
            'success': False, 'error': str(e),
            'airplanes': [], 'airplane_count': 0,
        }, status=500)


def get_airplane_details(request, icao24):
    """GET /api/airplane/<icao24>"""
    try:
        svc = get_services()
        details = svc.airplane_manager.get_airplane_details(icao24)
        if details:
            return JsonResponse({'success': True, 'airplane': details})
        return JsonResponse({'success': False, 'error': 'Airplane not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting airplane {icao24}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
