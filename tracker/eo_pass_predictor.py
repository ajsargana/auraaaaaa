"""
Universal EO Pass Predictor
============================
Uses the existing 50ms spatial-temporal index (DiskSpatialIndex.query_passes())
as the fast pass-calculation back-end.

Pipeline:
  1. query_passes(lat, lon, start, end, min_elev) → raw pass events (~50 ms)
  2. Filter to EO candidate NORAD IDs (from eo_satellite_resolver)
  3. Apply swath intersection check (point_in_swath) – true EO pass
  4. Apply daylight filter for optical sensors (if daylight_only=True)
  5. Score and rank each pass (sensor-aware weights)
  6. Return top max_results passes enriched with sensor metadata

Scoring weights per sensor type
--------------------------------
             elev   prox   swath   res   solar
SAR:         0.35   0.25   0.20   0.20   0.00   (all-weather, day+night)
optical:     0.35   0.20   0.10   0.10   0.25   (daylight critical)
thermal:     0.40   0.30   0.20   0.10   0.00   (day+night fine)
multispect:  0.35   0.20   0.15   0.15   0.15   (slight daylight pref)
weather:     0.30   0.30   0.40   0.00   0.00   (wide coverage priority)
lidar:       0.45   0.30   0.15   0.10   0.00
hyperspect:  0.35   0.25   0.20   0.20   0.00
_default:    0.35   0.25   0.20   0.20   0.00
"""

import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sensor-aware scoring weights
# ---------------------------------------------------------------------------
_WEIGHTS = {
    "SAR":           {"elev": 0.35, "prox": 0.25, "swath": 0.20, "res": 0.20, "solar": 0.00},
    "optical":       {"elev": 0.35, "prox": 0.20, "swath": 0.10, "res": 0.10, "solar": 0.25},
    "thermal":       {"elev": 0.40, "prox": 0.30, "swath": 0.20, "res": 0.10, "solar": 0.00},
    "multispectral": {"elev": 0.35, "prox": 0.20, "swath": 0.15, "res": 0.15, "solar": 0.15},
    "weather":       {"elev": 0.30, "prox": 0.30, "swath": 0.40, "res": 0.00, "solar": 0.00},
    "lidar":         {"elev": 0.45, "prox": 0.30, "swath": 0.15, "res": 0.10, "solar": 0.00},
    "hyperspectral": {"elev": 0.35, "prox": 0.25, "swath": 0.20, "res": 0.20, "solar": 0.00},
    "_default":      {"elev": 0.35, "prox": 0.25, "swath": 0.20, "res": 0.20, "solar": 0.00},
}


# ---------------------------------------------------------------------------
# Solar elevation helper
# ---------------------------------------------------------------------------
def _compute_solar_elevation(lat: float, lon: float, utc_time: datetime) -> float:
    """
    Return solar elevation (degrees) at (lat, lon) at utc_time.
    Uses Skyfield + de421.bsp if available, falls back to simple analytical model.
    Returns 0.0 on any failure.
    """
    try:
        import os
        bsp_candidates = [
            os.path.join(os.path.dirname(__file__), '..', 'de421.bsp'),
            '/d/SattTrack_converted/de421.bsp',
            'de421.bsp',
        ]
        bsp_path = None
        for p in bsp_candidates:
            if os.path.exists(p):
                bsp_path = p
                break

        if bsp_path:
            from skyfield.api import load, wgs84
            ts = load.timescale()
            eph = load(bsp_path)
            t = ts.from_datetime(utc_time.replace(tzinfo=timezone.utc))
            observer = wgs84.latlon(lat, lon)
            sun = eph['sun']
            earth = eph['earth']
            astrometric = (earth + observer).at(t).observe(sun)
            alt, _, _ = astrometric.apparent().altaz()
            return float(alt.degrees)
    except Exception:
        pass

    # Fallback: analytical solar elevation (±5° accuracy)
    try:
        doy = utc_time.timetuple().tm_yday
        hour_utc = utc_time.hour + utc_time.minute / 60.0
        # Solar declination
        decl = math.radians(23.45 * math.sin(math.radians(360 / 365 * (doy - 81))))
        # Hour angle
        lstm = 15.0 * round(lon / 15.0)       # local standard time meridian
        eot = _equation_of_time(doy)           # minutes
        lst = hour_utc + (lon - lstm) / 15.0 + eot / 60.0
        ha = math.radians(15.0 * (lst - 12.0))
        lat_r = math.radians(lat)
        sin_alt = (math.sin(lat_r) * math.sin(decl) +
                   math.cos(lat_r) * math.cos(decl) * math.cos(ha))
        return math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))
    except Exception:
        return 0.0


def _equation_of_time(doy: int) -> float:
    """Equation of time in minutes (approximate)."""
    b = math.radians(360 / 365 * (doy - 81))
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def _solar_score(solar_elevation: float) -> float:
    """Convert solar elevation (degrees) to 0–1 score."""
    if solar_elevation >= 10.0:
        return 1.0
    if solar_elevation >= 0.0:
        return solar_elevation / 10.0
    return 0.0


# ---------------------------------------------------------------------------
# Resolution score helper
# ---------------------------------------------------------------------------
def _resolution_score(swath_km: Optional[float]) -> float:
    """
    Invert swath width to approximate resolution score.
    Narrower swath → higher resolution → higher score.
    Clipped to [0, 1].
    """
    if swath_km is None or swath_km <= 0:
        return 0.5        # unknown – neutral
    # Score: 1.0 for ≤5 km swath, ~0 for ≥3000 km
    return max(0.0, min(1.0, 1.0 - (math.log10(swath_km) - math.log10(5)) /
                                     (math.log10(3000) - math.log10(5))))


# ---------------------------------------------------------------------------
# Main predictor
# ---------------------------------------------------------------------------

def predict_eo_passes(
    intent: dict,
    candidates: list[dict],
    satellite_manager,
    fov_db,           # EarthObservationSatellites (has point_in_swath())
    spatial_index,    # DiskSpatialIndex (may be None)
    max_results: int = 15,
) -> dict:
    """
    Predict EO satellite passes using the fast spatial index.

    Parameters
    ----------
    intent           : dict from extract_eo_pass_intent()
    candidates       : list from resolve_satellites()
    satellite_manager: SatelliteDataManager
    fov_db           : EarthObservationSatellites instance
    spatial_index    : DiskSpatialIndex instance (or None → Skyfield fallback)
    max_results      : maximum passes to return

    Returns
    -------
    {
      "passes"              : list[dict],
      "total_found"         : int,
      "satellites_checked"  : int,
      "location"            : dict,
      "time_hours"          : float,
      "filters"             : dict,
      "error"               : str | None,
    }
    """
    # ── Validate location ────────────────────────────────────────────────
    loc = intent.get("location")
    if not loc:
        return {
            "passes": [], "total_found": 0, "satellites_checked": 0,
            "location": None, "time_hours": intent.get("time_hours", 48),
            "filters": {}, "error": "No location specified or detected.",
        }

    obs_lat = float(loc["lat"])
    obs_lon = float(loc["lon"])
    time_hours = float(intent.get("time_hours", 48.0))
    min_elevation = float(intent.get("min_elevation", 10.0))
    daylight_only = intent.get("daylight_only", False)
    resolution_tier = intent.get("resolution_tier")

    now = datetime.now(timezone.utc)
    end_time = now + timedelta(hours=time_hours)

    # Build fast lookup: norad_id → metadata dict
    candidate_lookup: dict[int, dict] = {int(c["norad_id"]): c for c in candidates}
    candidate_ids = set(candidate_lookup.keys())

    # ── Query the fast pass index ────────────────────────────────────────
    raw_results = []
    index_used = False
    if spatial_index is not None:
        try:
            raw_results = spatial_index.query_passes(
                lat=obs_lat,
                lon=obs_lon,
                start_time=now,
                end_time=end_time,
                min_elevation=min_elevation,
            )
            index_used = True
            logger.info(f"[EOPredictor] Spatial index returned {len(raw_results)} satellites")
        except Exception as e:
            logger.warning(f"[EOPredictor] Spatial index query failed: {e} – using Skyfield fallback")

    if not index_used:
        # Skyfield fallback for when index isn't built yet
        raw_results = _skyfield_fallback(
            candidate_ids, satellite_manager, obs_lat, obs_lon,
            now, end_time, min_elevation,
        )

    # ── Filter to EO candidates + swath check ────────────────────────────
    all_passes = []
    satellites_checked = len(candidate_ids)

    for sat_result in raw_results:
        norad_id = int(sat_result["norad_id"])
        if norad_id not in candidate_ids:
            continue  # not an EO candidate for this query

        meta = candidate_lookup[norad_id]
        sensor_type = meta.get("sensor_type", "optical")
        weights = _WEIGHTS.get(sensor_type, _WEIGHTS["_default"])
        swath_km = meta.get("swath_km")

        for pass_event in sat_result.get("passes", []):
            max_elev = float(pass_event.get("max_elevation", 0))
            if max_elev < min_elevation:
                continue

            # ── Swath intersection check ──
            # For agile satellites (off_nadir_deg > 0) we use the max off-nadir
            # reach instead of the nadir-only swath geometry.
            off_nadir = meta.get("off_nadir_deg", 0) or 0
            alt_km_meta = meta.get("altitude_km") or 600.0
            if off_nadir > 0 and max_elev > 0:
                # Cross-track distance from observer to sub-satellite point
                cross_track_km = alt_km_meta / math.tan(math.radians(max_elev))
                # Maximum reach via off-nadir pointing
                max_reach_km = alt_km_meta * math.tan(math.radians(off_nadir))
                in_swath = cross_track_km <= max_reach_km
            else:
                in_swath = fov_db.point_in_swath(
                    norad_id=norad_id,
                    max_elevation_deg=max_elev,
                    satellite_alt_km=alt_km_meta,
                )
            if not in_swath:
                continue  # observer outside sensor footprint

            # ── Resolution tier filter ──
            if resolution_tier == "sub-meter" and (swath_km or 999) > 30:
                continue   # very narrow swath needed
            if resolution_tier == "coarse" and (swath_km or 0) < 200:
                continue   # need wide swath

            # ── Daylight filter ──
            rise_time_str = pass_event.get("start") or pass_event.get("rise_time")
            pass_utc = _parse_iso(rise_time_str) or now
            solar_elev = _compute_solar_elevation(obs_lat, obs_lon, pass_utc)
            is_daylight = solar_elev > -0.833  # astronomical civil twilight

            if daylight_only and not is_daylight:
                continue

            # ── Score ──
            elev_score  = min(1.0, max_elev / 90.0)
            # proximity: how close to overhead (90° = perfect)
            prox_score  = min(1.0, max_elev / 90.0)
            swath_score = _resolution_score(swath_km)
            res_score   = 1.0 - swath_score  # narrower swath = higher resolution
            s_score     = _solar_score(solar_elev) if weights["solar"] > 0 else 0.0

            score = (weights["elev"]  * elev_score +
                     weights["prox"]  * prox_score +
                     weights["swath"] * swath_score +
                     weights["res"]   * res_score +
                     weights["solar"] * s_score)

            score = round(score * 100, 1)

            # ── Build pass record ──
            duration_s = float(pass_event.get("duration_seconds", 0))

            pass_record = {
                # Core pass geometry
                "norad_id":           norad_id,
                "name":               meta.get("name", f"SAT-{norad_id}"),
                "rise_time":          _fmt(pass_event.get("start")),
                "set_time":           _fmt(pass_event.get("end")),
                "max_elevation":      round(max_elev, 1),
                "max_elevation_time": _fmt(pass_event.get("max_elevation_time")),
                "duration_minutes":   round(duration_s / 60, 1),
                "rise_azimuth":       round(float(pass_event.get("start_azimuth", 0)), 1),
                "set_azimuth":        round(float(pass_event.get("end_azimuth", 0)), 1),
                "score":              score,

                # Sensor metadata
                "sensor_type":        sensor_type,
                "constellation":      meta.get("constellation"),
                "agency":             meta.get("agency"),
                "swath_km":           swath_km,
                "resolution_m":       meta.get("resolution_m"),
                "altitude_km":        meta.get("altitude_km"),
                "use_cases":          meta.get("use_cases", []),
                "color":              meta.get("color", "#94a3b8"),
                "icon":               meta.get("icon", "🛰️"),

                # Daylight / solar
                "solar_elevation":    round(solar_elev, 1),
                "is_daylight":        is_daylight,
                "daylight_badge":     "☀️ Daylight" if is_daylight else "🌙 Night",
            }

            all_passes.append(pass_record)

    # ── Sort and cap ──────────────────────────────────────────────────────
    all_passes.sort(key=lambda p: (-p["score"], p["rise_time"] or ""))
    total_found = len(all_passes)
    top_passes = all_passes[:max_results]

    return {
        "passes":             top_passes,
        "total_found":        total_found,
        "satellites_checked": satellites_checked,
        "location":           loc,
        "time_hours":         time_hours,
        "filters": {
            "sensor_type":     intent.get("sensor_type"),
            "sensor_types":    intent.get("sensor_types", []),
            "specific_satellite": intent.get("specific_satellite"),
            "constellation":   intent.get("constellation"),
            "use_case":        intent.get("use_case"),
            "min_elevation":   min_elevation,
            "daylight_only":   daylight_only,
            "resolution_tier": resolution_tier,
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# Skyfield fallback (when spatial index not yet built)
# ---------------------------------------------------------------------------

def _skyfield_fallback(
    candidate_ids: set[int],
    satellite_manager,
    obs_lat: float,
    obs_lon: float,
    start_dt: datetime,
    end_dt: datetime,
    min_elevation: float,
) -> list[dict]:
    """
    Minimal Skyfield-based pass finder as fallback.
    Returns same structure as spatial_index.query_passes().
    """
    try:
        from skyfield.api import load, wgs84
        ts = load.timescale()
        observer = wgs84.latlon(obs_lat, obs_lon)
        t0 = ts.from_datetime(start_dt.replace(tzinfo=timezone.utc))
        t1 = ts.from_datetime(end_dt.replace(tzinfo=timezone.utc))
    except Exception as e:
        logger.error(f"[Skyfield fallback] Cannot initialize: {e}")
        return []

    results = []
    for norad_id in candidate_ids:
        sat_data = (satellite_manager.satellites.get(norad_id) or
                    satellite_manager.satellites.get(str(norad_id)))
        if not sat_data:
            continue
        try:
            from skyfield.api import EarthSatellite
            # Prefer the pre-built satellite_obj; fall back to TLE strings
            sat = sat_data.get("satellite_obj")
            if sat is None:
                tle1 = sat_data.get("tle1", sat_data.get("line1", ""))
                tle2 = sat_data.get("tle2", sat_data.get("line2", ""))
                if not tle1 or not tle2:
                    continue
                sat = EarthSatellite(tle1, tle2, sat_data.get("name", ""), ts)
            times, events = sat.find_events(observer, t0, t1,
                                            altitude_degrees=min_elevation)
            if not len(events):
                continue

            # Group into rise/peak/set triplets
            passes = []
            i = 0
            while i < len(events) - 1:
                if events[i] == 0:  # rise
                    rise_t = times[i].utc_datetime()
                    max_elev = 0.0
                    max_t = rise_t
                    set_t = rise_t
                    j = i + 1
                    while j < len(events):
                        if events[j] == 1:  # culmination
                            diff = sat - observer
                            topo = diff.at(times[j])
                            alt, _, _ = topo.altaz()
                            max_elev = float(alt.degrees)
                            max_t = times[j].utc_datetime()
                        elif events[j] == 2:  # set
                            set_t = times[j].utc_datetime()
                            break
                        j += 1

                    duration_s = (set_t - rise_t).total_seconds()
                    if duration_s >= 30 and max_elev >= min_elevation:
                        passes.append({
                            "start":             rise_t.isoformat(),
                            "end":               set_t.isoformat(),
                            "max_elevation":     round(max_elev, 1),
                            "max_elevation_time": max_t.isoformat(),
                            "duration_seconds":  duration_s,
                            "start_azimuth":     0.0,
                            "end_azimuth":       0.0,
                        })
                    i = j + 1
                else:
                    i += 1

            if passes:
                results.append({
                    "norad_id": norad_id,
                    "name":     sat_data.get("name", f"SAT-{norad_id}"),
                    "category": sat_data.get("category", "EO"),
                    "passes":   passes,
                })
        except Exception as e:
            logger.debug(f"[Skyfield fallback] NORAD {norad_id}: {e}")
            continue

    return results


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _fmt(ts: Optional[str]) -> Optional[str]:
    """Normalise ISO timestamp string (keep as-is if already valid)."""
    if not ts:
        return None
    try:
        dt = _parse_iso(ts)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else ts
    except Exception:
        return ts
