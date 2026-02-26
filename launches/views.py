"""
Launches views — upcoming rocket launches and analytics.
Mirrors /launches, /api/launches/* routes from the original Flask app.py.
"""
import logging
from django.http import JsonResponse
from django.shortcuts import render

from core.services import get_services

logger = logging.getLogger(__name__)


def launches_page(request):
    """GET /launches"""
    return render(request, 'launches.html')


def get_upcoming_launches(request):
    """GET /api/launches/upcoming"""
    try:
        svc = get_services()
        if not svc.launch_data_module:
            return JsonResponse({
                'success': False, 'error': 'Launch data module not initialized',
                'launches': [], 'total_count': 0,
            }, status=500)
        limit = int(request.GET.get('limit', 50))
        data = svc.launch_data_module.get_upcoming_launches(limit)
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error getting upcoming launches: {e}")
        return JsonResponse({
            'success': False, 'error': str(e),
            'launches': [], 'total_count': 0,
        }, status=500)


def get_launch_analytics(request):
    """GET /api/launches/analytics"""
    try:
        svc = get_services()
        if not svc.launch_data_module:
            return JsonResponse({'success': False, 'error': 'Launch data module not initialized'}, status=500)
        data = svc.launch_data_module.get_launch_analytics()
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error getting launch analytics: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
