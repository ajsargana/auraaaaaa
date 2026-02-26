"""
SAR Pass Prediction Engine
==========================
Pipeline stage 3 – given a parsed NLU intent, produce ranked SAR satellite
pass predictions using the existing Skyfield-based orbital mechanics.

Flow
----
  intent (from sar_nlu)
    → _collect_sar_satellites(satellite_manager)
    → _filter_by_nlu(satellites, intent)
    → _compute_passes(filtered_sats, lat, lon, time_hours)
    → _score_and_rank(all_passes)
    → top-N passes  (at least 10 where data allows)

Pass scoring weights
--------------------
  max_elevation       – higher = better view angle            (weight 40 %)
  sun_avoidance       – SAR works day/night, but cloud/RFI    (weight  0 %)
  swath_coverage      – wider swath → higher chance of target (weight 20 %)
  resolution          – finer resolution → higher quality     (weight 20 %)
  time_proximity      – sooner passes preferred               (weight 20 %)
"""

import logging
import math
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# Scoring weights (must sum to 1.0)
_WEIGHT_ELEVATION   = 0.35
_WEIGHT_SWATH       = 0.20
_WEIGHT_RESOLUTION  = 0.20
_WEIGHT_PROXIMITY   = 0.25

# Default prediction horizon when none supplied
DEFAULT_HOURS = 48.0
MAX_HOURS     = 168.0      # 7 days hard cap
MIN_ELEVATION = 10.0       # degrees

# How many results to return
TARGET_RESULTS = 10


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict_sar_passes(satellite_manager, intent: dict, max_results: int = TARGET_RESULTS) -> dict:
    """
    Main entry point for the SAR pass prediction pipeline.

    Parameters
    ----------
    satellite_manager : SatelliteDataManager instance (has .satellites dict)
    intent            : dict from sar_nlu.extract_sar_intent()
    max_results       : how many ranked passes to return (default 10)

    Returns
    -------
    {
        "passes"     : [ pass_record, ... ],   # max_results items
        "total_found": int,
        "satellites_checked": int,
        "location"   : {"name", "lat", "lon"},
        "time_hours" : float,
        "filters"    : {...},
    }
    """
    from tracker.sar_satellite_db import (
        SAR_SATELLITES,
        get_sar_norad_by_tle_name,
        filter_by_band,
        filter_by_agency,
    )

    location   = intent.get("location")
    time_hours = min(float(intent.get("time_hours", DEFAULT_HOURS)), MAX_HOURS)
    min_elev   = float(intent.get("min_elevation", MIN_ELEVATION))
    band_f     = intent.get("band_filter")
    agency_f   = intent.get("agency_filter")

    if location is None:
        # No location resolved – return empty with hint
        return {
            "passes": [],
            "total_found": 0,
            "satellites_checked": 0,
            "location": None,
            "time_hours": time_hours,
            "filters": {"band": band_f, "agency": agency_f},
            "error": "location_unknown",
        }

    lat = float(location["lat"])
    lon = float(location["lon"])

    # ── Step A: collect SAR satellites present in the live TLE data ───────
    sar_sats = _collect_sar_satellites(satellite_manager, SAR_SATELLITES, get_sar_norad_by_tle_name)

    # ── Step B: apply filters ─────────────────────────────────────────────
    candidate_ids = list(sar_sats.keys())

    if band_f:
        candidate_ids = filter_by_band(candidate_ids, band_f)
        # Also keep any extra matched ones from TLE-name fuzzy matching
        candidate_ids = [nid for nid in candidate_ids if nid in sar_sats]

    if agency_f:
        candidate_ids = filter_by_agency(candidate_ids, agency_f)
        candidate_ids = [nid for nid in candidate_ids if nid in sar_sats]

    if not candidate_ids:
        # If strict filters match nothing, fall back to all SAR sats found
        candidate_ids = list(sar_sats.keys())

    satellites_checked = len(candidate_ids)
    logger.info(f"[SAR-PRED] {satellites_checked} SAR candidates → computing passes")

    # ── Step C: compute passes for each candidate ─────────────────────────
    all_passes = []
    for norad_id in candidate_ids:
        sat_entry = sar_sats[norad_id]
        passes = _compute_passes_for_sat(
            satellite_manager, norad_id, lat, lon,
            time_hours=time_hours, min_elevation=min_elev
        )
        for p in passes:
            p["norad_id"]       = norad_id
            p["satellite_name"] = sat_entry["name"]
            p["sar_info"]       = sat_entry["sar_info"]
            p["category"]       = sat_entry["category"]
            p["color"]          = sat_entry.get("color", "#00b4d8")
        all_passes.extend(passes)

    # ── Step D: score and rank ─────────────────────────────────────────────
    scored = _score_and_rank(all_passes, now_utc=datetime.now(timezone.utc))
    top    = scored[:max_results]

    return {
        "passes":              top,
        "total_found":         len(all_passes),
        "satellites_checked":  satellites_checked,
        "location":            location,
        "time_hours":          time_hours,
        "filters": {
            "band":   band_f,
            "agency": agency_f,
        },
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect_sar_satellites(satellite_manager, SAR_SATELLITES, get_sar_norad_by_tle_name):
    """
    Cross-reference the live satellite_manager.satellites dict against the
    SAR database by NORAD ID and TLE name fragment.

    Returns
    -------
    dict  norad_id → {"name", "category", "color", "sar_info", "satellite_obj"}
    """
    result = {}

    for norad_id, sat_data in satellite_manager.satellites.items():
        # 1. Direct NORAD match
        if norad_id in SAR_SATELLITES:
            sar_info = SAR_SATELLITES[norad_id]
            result[norad_id] = {
                "name":          sar_info["name"],
                "category":      sat_data.get("category", "earth_observation"),
                "color":         sar_info.get("color", "#00b4d8"),
                "sar_info":      sar_info,
                "satellite_obj": sat_data.get("satellite_obj"),
            }
            continue

        # 2. TLE name fragment match
        tle_name   = sat_data.get("name", "")
        matched_id = get_sar_norad_by_tle_name(tle_name)
        if matched_id and matched_id in SAR_SATELLITES:
            sar_info = SAR_SATELLITES[matched_id]
            result[norad_id] = {
                "name":          sar_info["name"],
                "category":      sat_data.get("category", "earth_observation"),
                "color":         sar_info.get("color", "#00b4d8"),
                "sar_info":      sar_info,
                "satellite_obj": sat_data.get("satellite_obj"),
            }
            continue

        # 3. Keyword heuristic in TLE name (SAR, RADAR, SAR keywords)
        name_up = tle_name.upper()
        sar_keywords_tle = [
            "SAR", "RADARSAT", "TERRASAR", "TANDEM-X", "COSMO-SKYMED",
            "SENTINEL-1", "ALOS", "RISAT", "ICEYE", "CAPELLA", "UMBRA", "PAZ",
        ]
        if any(kw in name_up for kw in sar_keywords_tle):
            # Build a generic SAR info entry from the name
            band = "C"
            if any(x in name_up for x in ["TERRASAR", "TANDEM", "COSMO", "ICEYE", "CAPELLA", "UMBRA", "PAZ"]):
                band = "X"
            elif "ALOS" in name_up or "PALSAR" in name_up:
                band = "L"

            result[norad_id] = {
                "name":     tle_name.strip(),
                "category": sat_data.get("category", "earth_observation"),
                "color":    "#52B788",
                "sar_info": {
                    "name":           tle_name.strip(),
                    "constellation":  _guess_constellation(name_up),
                    "agency":         _guess_agency(name_up),
                    "country":        "Unknown",
                    "band":           band,
                    "frequency_ghz":  5.4 if band == "C" else 9.65,
                    "wavelength_cm":  5.6 if band == "C" else 3.1,
                    "modes": {
                        "StripMap": {"swath_km": 100, "resolution_m": 10, "look_angle_deg": (20, 45)},
                    },
                    "default_mode":   "StripMap",
                    "repeat_cycle_days": 12,
                    "altitude_km":    sat_data.get("altitude", 600),
                    "status":         "active",
                    "use_cases":      ["SAR imaging"],
                    "color":          "#52B788",
                    "icon":           "📡",
                },
                "satellite_obj": sat_data.get("satellite_obj"),
            }

    logger.info(f"[SAR-PRED] Found {len(result)} SAR satellites in live TLE data")
    return result


def _compute_passes_for_sat(satellite_manager, norad_id, lat, lon,
                             time_hours=48.0, min_elevation=10.0):
    """
    Use the existing SatelliteDataManager pass-prediction logic.
    Returns a list of pass dicts (skyfield-based).
    """
    try:
        if norad_id not in satellite_manager.satellites:
            return []

        sat_data  = satellite_manager.satellites[norad_id]
        satellite = sat_data.get("satellite_obj")
        if satellite is None:
            return []

        from skyfield.api import wgs84

        ts       = satellite_manager.ts
        t0       = ts.now()
        t1_days  = time_hours / 24.0

        observer = wgs84.latlon(lat, lon)

        # Use Skyfield's find_events for accurate pass timing
        try:
            t_events, events = satellite.find_events(
                observer, t0, ts.tt_jd(t0.tt + t1_days),
                altitude_degrees=min_elevation
            )
        except Exception as fe:
            logger.debug(f"find_events failed for {norad_id}: {fe}")
            return _fallback_passes(satellite, observer, ts, t0, t1_days, min_elevation)

        # Group events: 0=rise, 1=culmination, 2=set
        passes = []
        i = 0
        while i < len(events):
            if events[i] == 0:   # rise
                rise_t = t_events[i]
                culm_t = None
                set_t  = None
                max_el = 0.0
                j = i + 1
                while j < len(events) and events[j] != 0:
                    if events[j] == 1:
                        culm_t = t_events[j]
                        # Calculate elevation at culmination
                        diff = satellite - observer
                        topo = diff.at(culm_t)
                        alt, az, _ = topo.altaz()
                        max_el = float(alt.degrees)
                    elif events[j] == 2:
                        set_t = t_events[j]
                    j += 1
                i = j

                if set_t is None or max_el < min_elevation:
                    continue

                # Duration
                dur_s = (set_t.tt - rise_t.tt) * 86400.0

                # Rise azimuth
                diff_rise = satellite - observer
                topo_rise = diff_rise.at(rise_t)
                _, az_rise, _ = topo_rise.altaz()

                # Set azimuth
                topo_set = diff_rise.at(set_t)
                _, az_set, _ = topo_set.altaz()

                # Look angle at culmination (off-nadir angle)
                look_angle = _compute_look_angle(satellite, observer, culm_t if culm_t else rise_t)

                rise_utc = rise_t.utc_datetime()
                set_utc  = set_t.utc_datetime()

                passes.append({
                    "rise_time":     rise_utc.isoformat(),
                    "set_time":      set_utc.isoformat(),
                    "max_elevation": round(max_el, 2),
                    "duration_s":    round(dur_s, 1),
                    "rise_azimuth":  round(float(az_rise.degrees), 1),
                    "set_azimuth":   round(float(az_set.degrees), 1),
                    "look_angle":    round(look_angle, 2),
                })
            else:
                i += 1

        return passes

    except Exception as e:
        logger.warning(f"[SAR-PRED] Pass computation error for NORAD {norad_id}: {e}")
        return []


def _fallback_passes(satellite, observer, ts, t0, t1_days, min_elevation):
    """
    Coarse sampling fallback when find_events is unavailable/fails.
    Samples every 5 minutes and looks for elevation crossings.
    """
    passes = []
    try:
        from skyfield.api import wgs84
        n_steps = int(t1_days * 24 * 12)   # every 5 minutes
        in_pass = False
        rise_t = None
        max_el = 0.0
        culm_t = None

        for step in range(n_steps):
            t = ts.tt_jd(t0.tt + step / (24 * 12))
            diff = satellite - observer
            topo = diff.at(t)
            alt, az, _ = topo.altaz()
            el = float(alt.degrees)

            if el >= min_elevation:
                if not in_pass:
                    in_pass = True
                    rise_t  = t
                    max_el  = el
                    culm_t  = t
                elif el > max_el:
                    max_el = el
                    culm_t = t
            else:
                if in_pass:
                    in_pass = False
                    set_t   = t
                    dur_s   = (set_t.tt - rise_t.tt) * 86400.0
                    look_angle = _compute_look_angle(satellite, observer, culm_t)

                    diff_rise = satellite - observer
                    topo_rise = diff_rise.at(rise_t)
                    _, az_rise, _ = topo_rise.altaz()
                    topo_set  = diff_rise.at(set_t)
                    _, az_set, _ = topo_set.altaz()

                    passes.append({
                        "rise_time":     rise_t.utc_datetime().isoformat(),
                        "set_time":      set_t.utc_datetime().isoformat(),
                        "max_elevation": round(max_el, 2),
                        "duration_s":    round(dur_s, 1),
                        "rise_azimuth":  round(float(az_rise.degrees), 1),
                        "set_azimuth":   round(float(az_set.degrees), 1),
                        "look_angle":    round(look_angle, 2),
                    })
    except Exception as e:
        logger.warning(f"[SAR-PRED] Fallback pass calc failed: {e}")

    return passes


def _compute_look_angle(satellite, observer, t):
    """
    Approximate off-nadir look angle from observer to satellite ground track.
    Uses the nadir angle formula: sin(look) = dist * sin(90-el) / alt_km
    """
    try:
        diff = satellite - observer
        topo = diff.at(t)
        alt_deg, _, distance = topo.altaz()
        el_rad   = math.radians(float(alt_deg.degrees))
        look_rad = math.asin(math.cos(el_rad))   # off-nadir ≈ 90° - elevation
        return math.degrees(look_rad)
    except Exception:
        return 0.0


def _score_and_rank(passes: list, now_utc: datetime) -> list:
    """
    Score each pass and sort descending.
    Score = weighted sum of normalised sub-scores.
    """
    if not passes:
        return []

    # Pre-compute ranges for normalisation
    elevs   = [p["max_elevation"] for p in passes]
    max_el  = max(elevs) if elevs else 90.0
    min_el  = min(elevs) if elevs else 0.0

    swaths = []
    resols = []
    for p in passes:
        sar = p.get("sar_info", {})
        mode = sar.get("modes", {}).get(sar.get("default_mode", ""), {})
        swaths.append(float(mode.get("swath_km", 100)))
        resols.append(float(mode.get("resolution_m", 10)))

    max_sw = max(swaths) if swaths else 500.0
    max_res = max(resols) if resols else 100.0

    now_ts = now_utc.timestamp()

    # Max future time for proximity normalisation (end of window)
    times = []
    for p in passes:
        try:
            rt = datetime.fromisoformat(p["rise_time"].replace("Z", "+00:00"))
            times.append(rt.timestamp())
        except Exception:
            times.append(now_ts)

    max_future = max(times) if times else now_ts + 86400 * 2

    for i, p in enumerate(passes):
        el_norm  = (p["max_elevation"] - min_el) / (max_el - min_el + 1e-9)
        sw_norm  = swaths[i] / (max_sw + 1e-9)
        # Finer resolution is better → invert
        res_norm = 1.0 - resols[i] / (max_res + 1e-9)
        # Earlier = higher score
        try:
            rt_ts = datetime.fromisoformat(p["rise_time"].replace("Z", "+00:00")).timestamp()
        except Exception:
            rt_ts = now_ts
        prox_norm = 1.0 - (rt_ts - now_ts) / (max_future - now_ts + 1e-9)
        prox_norm = max(0.0, min(1.0, prox_norm))

        score = (
            _WEIGHT_ELEVATION  * el_norm +
            _WEIGHT_SWATH      * sw_norm +
            _WEIGHT_RESOLUTION * res_norm +
            _WEIGHT_PROXIMITY  * prox_norm
        )
        p["score"] = round(score * 100, 1)    # 0–100

        # Human-readable time
        try:
            rt  = datetime.fromisoformat(p["rise_time"].replace("Z", "+00:00"))
            sett = datetime.fromisoformat(p["set_time"].replace("Z", "+00:00"))
            p["rise_time_human"] = rt.strftime("%Y-%m-%d %H:%M UTC")
            p["set_time_human"]  = sett.strftime("%Y-%m-%d %H:%M UTC")
            p["duration_min"]    = round(p["duration_s"] / 60.0, 1)
        except Exception:
            p["rise_time_human"] = p.get("rise_time", "")
            p["set_time_human"]  = p.get("set_time", "")
            p["duration_min"]    = round(p.get("duration_s", 0) / 60.0, 1)

    passes.sort(key=lambda x: x["score"], reverse=True)
    return passes


# ---------------------------------------------------------------------------
# Agency / constellation guessing for unknown SAR sats found by name
# ---------------------------------------------------------------------------

def _guess_constellation(name_upper: str) -> str:
    for kw, c in [
        ("SENTINEL", "Sentinel-1"), ("RADARSAT", "RADARSAT"),
        ("TERRASAR", "TerraSAR-X"), ("TANDEM", "TerraSAR-X"),
        ("COSMO", "COSMO-SkyMed"), ("ALOS", "ALOS"),
        ("ICEYE", "ICEYE"), ("CAPELLA", "Capella"), ("UMBRA", "Umbra"),
    ]:
        if kw in name_upper:
            return c
    return "Unknown"


def _guess_agency(name_upper: str) -> str:
    for kw, a in [
        ("SENTINEL", "ESA"), ("RADARSAT", "CSA"),
        ("TERRASAR", "DLR"), ("TANDEM", "DLR"),
        ("COSMO", "ASI"), ("ALOS", "JAXA"), ("PALSAR", "JAXA"),
        ("RISAT", "ISRO"), ("ICEYE", "ICEYE"),
        ("CAPELLA", "Capella Space"), ("UMBRA", "Umbra Lab"),
        ("PAZ", "Hisdesat"),
    ]:
        if kw in name_upper:
            return a
    return "Unknown"
