"""
Core views — landing page, facts, chat, status, preferences, test route.
Mirrors the corresponding @app.route handlers from the original Flask app.py.
"""
import os
import random
import logging
from datetime import datetime, timezone

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods

from core.services import get_services

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


# ── Page views ───────────────────────────────────────────────────────

def landing(request):
    """Landing page  (was Flask GET /)"""
    return render(request, 'landing.html')


# ── API views ────────────────────────────────────────────────────────

def random_space_fact(request):
    """GET /api/random-space-fact"""
    try:
        facts_file = os.path.join(DATA_DIR, 'space_facts.txt')
        if not os.path.exists(facts_file):
            return JsonResponse({'success': False, 'error': 'Space facts file not found'}, status=404)

        with open(facts_file, 'r', encoding='utf-8') as f:
            facts = [line.strip() for line in f.readlines() if line.strip()]

        if not facts:
            return JsonResponse({'success': False, 'error': 'No facts available'}, status=404)

        return JsonResponse({
            'success': True,
            'fact': random.choice(facts),
            'total_facts': len(facts),
        })
    except Exception as e:
        logger.error(f"Error getting random space fact: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def random_satellite_fact(request):
    """GET /api/random-satellite-fact"""
    try:
        facts_file = os.path.join(DATA_DIR, 'satellite_facts.txt')
        if not os.path.exists(facts_file):
            return JsonResponse({'success': False, 'error': 'Satellite facts file not found'}, status=404)

        with open(facts_file, 'r', encoding='utf-8') as f:
            facts = [line.strip() for line in f.readlines() if line.strip()]

        if not facts:
            return JsonResponse({'success': False, 'error': 'No facts available'}, status=404)

        return JsonResponse({
            'success': True,
            'fact': random.choice(facts),
            'total_facts': len(facts),
        })
    except Exception as e:
        logger.error(f"Error getting random satellite fact: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def chat(request):
    """POST /api/chat"""
    import json
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        chat_type    = data.get('chatType', 'agent')
        # Optional browser-supplied coordinates (sent by the frontend)
        browser_lat  = data.get('lat')
        browser_lon  = data.get('lon')

        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)

        # ── Universal EO / SAR pipeline intercept ────────────────────
        from core.eo_pass_nlu import extract_eo_pass_intent, describe_eo_intent
        from tracker.eo_satellite_resolver import resolve_satellites
        from tracker.eo_pass_predictor import predict_eo_passes

        blat = float(browser_lat) if browser_lat is not None else None
        blon = float(browser_lon) if browser_lon is not None else None

        intent = extract_eo_pass_intent(user_message, browser_lat=blat, browser_lon=blon)

        if intent["is_eo_pass_query"]:
            try:
                svc = get_services()
                if not svc.satellite_manager or len(svc.satellite_manager.satellites) == 0:
                    svc.satellite_manager.load_tle_data()

                # Use cached FOV database from services singleton
                fov_db = svc.fov_db
                if fov_db is None:
                    from tracker.satellite_fov_data import EarthObservationSatellites
                    fov_db = EarthObservationSatellites()

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
                    max_results=15,
                )

                # ── Build human-readable text reply ─────────────────
                passes_found = result["total_found"]
                sats_checked = result["satellites_checked"]
                loc_name = (result["location"] or {}).get("name", "the selected location")
                sensor_label = {
                    "SAR": "SAR / Radar", "optical": "Optical",
                    "thermal": "Thermal IR", "multispectral": "Multispectral",
                    "hyperspectral": "Hyperspectral", "lidar": "LiDAR",
                    "weather": "Weather Sensor",
                }.get(intent.get("sensor_type"), "EO")
                specific_sat = intent.get("specific_satellite")
                if specific_sat:
                    reply_intro = f"I found **{passes_found}** pass(es) for **{specific_sat}** over {loc_name}"
                elif intent.get("constellation"):
                    reply_intro = f"I found **{passes_found}** pass(es) from the **{intent['constellation']}** constellation over {loc_name}"
                elif intent.get("use_case"):
                    reply_intro = f"For **{intent['use_case']}** mapping over {loc_name}, I found **{passes_found}** suitable satellite pass(es)"
                else:
                    reply_intro = f"I found **{passes_found}** {sensor_label} satellite pass(es) over {loc_name}"

                if passes_found > 0:
                    top_pass = result["passes"][0]
                    top_name = top_pass.get("name", "")
                    top_elev = top_pass.get("max_elevation", 0)
                    top_rise = top_pass.get("rise_time", "")
                    try:
                        top_rise_fmt = datetime.fromisoformat(top_rise.replace("Z", "+00:00")).strftime("%H:%M UTC")
                    except Exception:
                        top_rise_fmt = top_rise[:16] if top_rise else "—"
                    text_reply = (
                        f"{reply_intro} in the next {int(result['time_hours'])} hours, "
                        f"checking {sats_checked} satellites with swath intersection verification.\n\n"
                        f"🏆 Best pass: **{top_name}** at {top_rise_fmt} — {top_elev:.0f}° max elevation.\n\n"
                        f"Tap **View Passes** to see the full ranked list and track on the globe."
                    )
                else:
                    text_reply = (
                        f"{reply_intro} in the next {int(result['time_hours'])} hours "
                        f"that fall within the sensor's swath coverage area. "
                        f"Try increasing the time window or selecting a wider-swath sensor type."
                    )

                eo_response = {
                    "type":               "eo_passes",
                    "intent_summary":     describe_eo_intent(intent),
                    "passes":             result["passes"],
                    "total_found":        result["total_found"],
                    "satellites_checked": result["satellites_checked"],
                    "location":           result["location"],
                    "time_hours":         result["time_hours"],
                    "filters":            result["filters"],
                    "error":              result.get("error"),
                    "text_reply":         text_reply,
                }

                return JsonResponse({
                    'response':      json.dumps(eo_response),
                    'chatType':      chat_type,
                    'isEOPassQuery': True,
                    # backward-compat: keep isSARQuery for SAR sensor type
                    'isSARQuery':    intent.get("is_sar_query", False),
                    'timestamp':     datetime.now().isoformat(),
                })

            except Exception as eo_err:
                import traceback
                logger.error(f"EO pass pipeline error: {eo_err}\n{traceback.format_exc()}")
                # Return a structured error to the frontend so the user gets useful feedback
                loc_name = (intent.get("location") or {}).get("name", "the specified location")
                eo_error_response = {
                    "type":           "eo_passes",
                    "intent_summary": describe_eo_intent(intent),
                    "passes":         [],
                    "total_found":    0,
                    "satellites_checked": 0,
                    "location":       intent.get("location"),
                    "time_hours":     intent.get("time_hours", 48),
                    "filters":        {},
                    "error":          "pipeline_error",
                    "text_reply":     (
                        f"I recognised your EO pass query for {loc_name}, but encountered an "
                        f"internal error while running the prediction pipeline. "
                        f"Please ensure the cache has finished building (check /api/spatial-index/status) "
                        f"and try again."
                    ),
                }
                return JsonResponse({
                    'response':      json.dumps(eo_error_response),
                    'chatType':      chat_type,
                    'isEOPassQuery': True,
                    'isSARQuery':    intent.get("is_sar_query", False),
                    'timestamp':     datetime.now().isoformat(),
                })

        # ── Default LLM path ──────────────────────────────────────────
        from core.ai_chat_module import process_chat_message
        response = process_chat_message(user_message, chat_type)

        return JsonResponse({
            'response':   response,
            'chatType':   chat_type,
            'isSARQuery': False,
            'timestamp':  datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return JsonResponse({
            'error':    'Failed to process chat message',
            'response': 'Sorry, I encountered an issue. Please try again.',
        }, status=500)


def status(request):
    """GET /api/status"""
    try:
        svc = get_services()
        st = svc.satellite_manager.get_status()

        priority_missions = ['LANDSAT', 'SENTINEL', 'WORLDVIEW', 'SWARM']
        priority_satellites = []
        for norad_id, sat in svc.satellite_manager.satellites.items():
            if any(m in sat['name'].upper() for m in priority_missions):
                priority_satellites.append({
                    'norad_id': norad_id,
                    'name': sat['name'],
                    'category': sat['category'],
                })

        return JsonResponse({
            'success': True,
            'data': {
                'satellites_loaded': st['satellites_loaded'],
                'last_update': st['last_update'],
                'categories': st['categories'],
                'priority_satellites': priority_satellites,
                'priority_count': len(priority_satellites),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'message': f"Tracking {st['satellites_loaded']} satellites ({len(priority_satellites)} priority missions)",
            },
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def weather_key(request):
    """GET /api/weather-key"""
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    if not api_key:
        return JsonResponse({'error': 'OpenWeatherMap API key not configured'}, status=503)
    return JsonResponse({'api_key': api_key})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def user_preferences(request):
    """GET/POST /api/user/preferences"""
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'preferences': {
                'location': {'lat': 0, 'lon': 0, 'alt': 0},
                'update_interval': 10,
            },
        })
    else:
        return JsonResponse({'success': True, 'message': 'Preferences saved'})


def test_view(request):
    """GET /test"""
    return HttpResponse("[OK] Test route works!")
