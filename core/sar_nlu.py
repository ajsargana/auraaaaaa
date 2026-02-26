"""
SAR Pass NLU – Natural Language Understanding for SAR satellite pass queries
============================================================================
Pipeline stage 1: parse the user's free-text query and extract:

  {
    "is_sar_query"   : bool,
    "sensor_type"    : "SAR",
    "location"       : {"name": str, "lat": float, "lon": float} | None,
    "time_hours"     : float,           # prediction window (default 48 h)
    "band_filter"    : str | None,      # "C" | "X" | "L" | None
    "agency_filter"  : str | None,
    "constellation"  : str | None,
    "min_elevation"  : float,           # degrees (default 10°)
    "raw_time_text"  : str | None,
  }

Location resolution order:
  1. Explicit lat/lon in message ("40.7N, 74W")
  2. Well-known city / region name  → built-in gazetteer
  3. "my location" / "here"         → returns None so caller can use
     the browser-supplied coords sent with the request.
"""

import re
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SAR intent keywords
# ---------------------------------------------------------------------------
_SAR_PATTERNS = [
    r"\bsar\b",
    r"synthetic\s+aperture\s+radar",
    r"radar\s+satellite",
    r"sentinel[\s\-]1",
    r"radarsat",
    r"terrasar",
    r"tandem[\s\-]x",
    r"cosmo[\s\-]skymed",
    r"alos[\s\-]?2?",
    r"\bpalsar\b",
    r"\brisat\b",
    r"\biceye\b",
    r"capella\s+sat",
    r"\bumbra\b",
    r"\bpaz\b",
    r"[clxs][\s\-]band\s+radar",
    r"sar\s+(pass|coverage|satellite|image|imagery)",
    r"(which|what|any)\s+sar",
]

_SAR_PASS_PATTERNS = [
    r"\bpass(es)?\b",
    r"\boverhead\b",
    r"\boverfl(y|ies|ying)\b",
    r"\bcover(age|ing|s)?\b",
    r"\bacquisition\b",
    r"\brevisit\b",
    r"\bwhen\b.*\bsar\b",
    r"\bsar\b.*\bwhen\b",
    r"\bnext\s+(sar|radar)",
    r"\bschedule\b",
    r"\bvisit\b",
]

# ---------------------------------------------------------------------------
# Mini gazetteer: city/region name → (lat, lon)
# (lowercase → coordinates)
# ---------------------------------------------------------------------------
_GAZETTEER = {
    # Americas
    "new york":         (40.7128, -74.0060),
    "new york city":    (40.7128, -74.0060),
    "nyc":              (40.7128, -74.0060),
    "los angeles":      (34.0522, -118.2437),
    "la":               (34.0522, -118.2437),
    "chicago":          (41.8781, -87.6298),
    "houston":          (29.7604, -95.3698),
    "miami":            (25.7617, -80.1918),
    "san francisco":    (37.7749, -122.4194),
    "seattle":          (47.6062, -122.3321),
    "washington dc":    (38.9072, -77.0369),
    "toronto":          (43.6532, -79.3832),
    "montreal":         (45.5017, -73.5673),
    "vancouver":        (49.2827, -123.1207),
    "mexico city":      (19.4326, -99.1332),
    "bogota":           (-4.7110, -74.0721),
    "lima":             (-12.0464, -77.0428),
    "santiago":         (-33.4489, -70.6693),
    "buenos aires":     (-34.6037, -58.3816),
    "sao paulo":        (-23.5505, -46.6333),
    "rio de janeiro":   (-22.9068, -43.1729),
    # Europe
    "london":           (51.5074, -0.1278),
    "paris":            (48.8566, 2.3522),
    "berlin":           (52.5200, 13.4050),
    "madrid":           (40.4168, -3.7038),
    "rome":             (41.9028, 12.4964),
    "amsterdam":        (52.3676, 4.9041),
    "brussels":         (50.8503, 4.3517),
    "vienna":           (48.2082, 16.3738),
    "warsaw":           (52.2297, 21.0122),
    "stockholm":        (59.3293, 18.0686),
    "oslo":             (59.9139, 10.7522),
    "helsinki":         (60.1699, 24.9384),
    "zurich":           (47.3769, 8.5417),
    "athens":           (37.9838, 23.7275),
    "lisbon":           (38.7223, -9.1393),
    "kiev":             (50.4501, 30.5234),
    "moscow":           (55.7558, 37.6176),
    "istanbul":         (41.0082, 28.9784),
    # Middle East
    "dubai":            (25.2048, 55.2708),
    "abu dhabi":        (24.4539, 54.3773),
    "riyadh":           (24.7136, 46.6753),
    "doha":             (25.2854, 51.5310),
    "tel aviv":         (32.0853, 34.7818),
    "tehran":           (35.6892, 51.3890),
    "baghdad":          (33.3152, 44.3661),
    "cairo":            (30.0444, 31.2357),
    # Asia
    "delhi":            (28.6139, 77.2090),
    "new delhi":        (28.6139, 77.2090),
    "mumbai":           (19.0760, 72.8777),
    "bangalore":        (12.9716, 77.5946),
    "kolkata":          (22.5726, 88.3639),
    "beijing":          (39.9042, 116.4074),
    "shanghai":         (31.2304, 121.4737),
    "hong kong":        (22.3193, 114.1694),
    "tokyo":            (35.6762, 139.6503),
    "osaka":            (34.6937, 135.5023),
    "seoul":            (37.5665, 126.9780),
    "bangkok":          (13.7563, 100.5018),
    "singapore":        (1.3521, 103.8198),
    "jakarta":          (-6.2088, 106.8456),
    "kuala lumpur":     (3.1390, 101.6869),
    "karachi":          (24.8607, 67.0011),
    "lahore":           (31.5497, 74.3436),
    "dhaka":            (23.8103, 90.4125),
    "colombo":          (6.9271, 79.8612),
    "yangon":           (16.8661, 96.1951),
    "hanoi":            (21.0285, 105.8542),
    "ho chi minh city": (10.8231, 106.6297),
    "manila":           (14.5995, 120.9842),
    "taipei":           (25.0330, 121.5654),
    # Africa
    "nairobi":          (-1.2921, 36.8219),
    "lagos":            (6.5244, 3.3792),
    "accra":            (5.6037, -0.1870),
    "johannesburg":     (-26.2041, 28.0473),
    "cape town":        (-33.9249, 18.4241),
    "addis ababa":      (9.1450, 40.4897),
    "dar es salaam":    (-6.7924, 39.2083),
    "khartoum":         (15.5007, 32.5599),
    "casablanca":       (33.5731, -7.5898),
    "tunis":            (36.8065, 10.1815),
    "algiers":          (36.7372, 3.0865),
    "kinshasa":         (-4.4419, 15.2663),
    "luanda":           (-8.8399, 13.2894),
    "dakar":            (14.6928, -17.4467),
    # Oceania
    "sydney":           (-33.8688, 151.2093),
    "melbourne":        (-37.8136, 144.9631),
    "brisbane":         (-27.4698, 153.0251),
    "perth":            (-31.9505, 115.8605),
    "auckland":         (-36.8485, 174.7633),
    # Arctic / Antarctic reference
    "north pole":       (90.0, 0.0),
    "south pole":       (-90.0, 0.0),
}

# ---------------------------------------------------------------------------
# Time pattern helpers
# ---------------------------------------------------------------------------
_TIME_PATTERNS = [
    (r"(\d+(?:\.\d+)?)\s*hours?",       lambda m: float(m.group(1))),
    (r"(\d+(?:\.\d+)?)\s*hrs?",         lambda m: float(m.group(1))),
    (r"(\d+(?:\.\d+)?)\s*days?",        lambda m: float(m.group(1)) * 24),
    (r"next\s+(\d+(?:\.\d+)?)\s*hours?",lambda m: float(m.group(1))),
    (r"next\s+(\d+(?:\.\d+)?)\s*days?", lambda m: float(m.group(1)) * 24),
    (r"today",                           lambda m: 24.0),
    (r"tonight",                         lambda m: 12.0),
    (r"tomorrow",                        lambda m: 48.0),
    (r"this\s+week",                     lambda m: 168.0),
    (r"(\d+)\s*h\b",                    lambda m: float(m.group(1))),
]

# ---------------------------------------------------------------------------
# Band filter keywords
# ---------------------------------------------------------------------------
_BAND_PATTERNS = {
    "C": [r"\bc[\s-]?band\b", r"\bsentinel[\s-]?1\b", r"\bradarsat\b", r"\brisat\b"],
    "X": [r"\bx[\s-]?band\b", r"\bterrasar\b", r"\btandem\b", r"\bcosmo\b", r"\biceye\b", r"\bcapella\b", r"\bumbra\b", r"\bpaz\b"],
    "L": [r"\bl[\s-]?band\b", r"\balos\b", r"\bpalsar\b"],
    "S": [r"\bs[\s-]?band\b"],
}

# Agency filter keywords
_AGENCY_PATTERNS = {
    "ESA":    [r"\besa\b", r"\beurope[an]*\b"],
    "NASA":   [r"\bnasa\b"],
    "JAXA":   [r"\bjaxa\b", r"\bjapan\b"],
    "DLR":    [r"\bdlr\b", r"\bgerma[ny]\b"],
    "CSA":    [r"\bcsa\b", r"\bcanad[ia]\b"],
    "ISRO":   [r"\bisro\b", r"\bindia[n]*\b"],
    "ASI":    [r"\basi\b", r"\bital[y|ian]\b"],
    "ICEYE":  [r"\biceye\b"],
    "Capella":[r"\bcapella\b"],
    "Umbra":  [r"\bumbra\b"],
}


# ---------------------------------------------------------------------------
# Core NLU function
# ---------------------------------------------------------------------------

def extract_sar_intent(user_input: str, browser_lat: float = None, browser_lon: float = None) -> dict:
    """
    Parse user_input and return a structured SAR query dict.

    Parameters
    ----------
    user_input   : raw user message from the chat panel
    browser_lat  : latitude supplied by the browser (or None)
    browser_lon  : longitude supplied by the browser (or None)

    Returns
    -------
    dict with keys: is_sar_query, sensor_type, location, time_hours,
                    band_filter, agency_filter, min_elevation, raw_time_text
    """
    txt = user_input.strip()
    low = txt.lower()

    result = {
        "is_sar_query":  False,
        "sensor_type":   "SAR",
        "location":      None,
        "time_hours":    48.0,      # default 48-hour window
        "band_filter":   None,
        "agency_filter": None,
        "constellation": None,
        "min_elevation": 10.0,      # degrees
        "raw_time_text": None,
        "use_browser_location": False,
    }

    # ── 1. Detect SAR intent ─────────────────────────────────────────────
    sar_hit = any(re.search(p, low) for p in _SAR_PATTERNS)
    pass_hit = any(re.search(p, low) for p in _SAR_PASS_PATTERNS)

    if not (sar_hit or pass_hit):
        return result          # not a SAR query

    result["is_sar_query"] = True

    # ── 2. Extract location ──────────────────────────────────────────────
    result["location"] = _extract_location(low, browser_lat, browser_lon, result)

    # ── 3. Extract time window ───────────────────────────────────────────
    for pattern, converter in _TIME_PATTERNS:
        m = re.search(pattern, low)
        if m:
            try:
                hours = converter(m)
                if 1 <= hours <= 720:        # 1 hour – 30 days
                    result["time_hours"] = hours
                    result["raw_time_text"] = m.group(0)
            except Exception:
                pass
            break

    # ── 4. Extract band filter ───────────────────────────────────────────
    for band, patterns in _BAND_PATTERNS.items():
        if any(re.search(p, low) for p in patterns):
            result["band_filter"] = band
            break

    # ── 5. Extract agency / constellation filter ──────────────────────────
    for agency, patterns in _AGENCY_PATTERNS.items():
        if any(re.search(p, low) for p in patterns):
            result["agency_filter"] = agency
            break

    # ── 6. Extract min elevation preference ─────────────────────────────
    elev_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:degree|deg|°)\s*(?:elevation|elev)", low)
    if elev_m:
        try:
            result["min_elevation"] = float(elev_m.group(1))
        except Exception:
            pass

    logger.info(f"[SAR-NLU] Parsed intent: {result}")
    return result


# ---------------------------------------------------------------------------
# Location helpers
# ---------------------------------------------------------------------------

def _extract_location(low: str, browser_lat, browser_lon, result: dict):
    """
    Try to resolve location from text.
    Returns {"name": ..., "lat": ..., "lon": ...} or None (use browser).
    """

    # a) explicit lat/lon like "40.7, -74.0" or "40.7N 74W"
    coord_m = re.search(
        r"(-?\d{1,3}(?:\.\d+)?)\s*°?\s*([NSns])?\s*[,/\s]+\s*(-?\d{1,3}(?:\.\d+)?)\s*°?\s*([EWew])?",
        low,
    )
    if coord_m:
        try:
            lat = float(coord_m.group(1))
            if coord_m.group(2) and coord_m.group(2).upper() == "S":
                lat = -lat
            lon = float(coord_m.group(3))
            if coord_m.group(4) and coord_m.group(4).upper() == "W":
                lon = -lon
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return {"name": f"{lat:.4f}°, {lon:.4f}°", "lat": lat, "lon": lon}
        except Exception:
            pass

    # b) "my location" / "here" / "current location" → use browser coords
    my_loc_patterns = [
        r"\bmy\s+location\b", r"\bmy\s+position\b",
        r"\bhere\b", r"\bwhere\s+i\s+am\b",
        r"\bcurrent\s+location\b", r"\bcurrent\s+position\b",
        r"\bmy\s+place\b",
    ]
    if any(re.search(p, low) for p in my_loc_patterns):
        if browser_lat is not None and browser_lon is not None:
            return {"name": "Your Location", "lat": browser_lat, "lon": browser_lon}
        result["use_browser_location"] = True
        return None        # caller must supply coords

    # c) "over <city>" / "above <city>" / "for <city>" / plain city name
    # Strip common prepositions to isolate the place name
    for prep_pattern in [
        r"(?:over|above|around|near|for|at|in|from)\s+([a-z][a-z\s\-']{2,40}?)(?:\s+in\s+the\s+next|\s+over|\s+for|\s+during|$|\?|,|\.|;)",
        r"(?:pass(?:es)?\s+over)\s+([a-z][a-z\s\-']{2,40?}?)(?:\s+|\?|$|,)",
        r"location\s+(?:of|:)?\s+([a-z][a-z\s\-']{2,40}?)(?:\s+|\?|$|,|\.)",
    ]:
        m = re.search(prep_pattern, low)
        if m:
            candidate = m.group(1).strip().rstrip(".,?!;")
            loc = _gazetteer_lookup(candidate)
            if loc:
                return loc

    # d) plain city name anywhere in the text (iterate gazetteer longest-first)
    sorted_cities = sorted(_GAZETTEER.keys(), key=len, reverse=True)
    for city in sorted_cities:
        if re.search(r"\b" + re.escape(city) + r"\b", low):
            lat, lon = _GAZETTEER[city]
            return {"name": city.title(), "lat": lat, "lon": lon}

    # e) fallback – no location found; caller will use browser coords
    if browser_lat is not None and browser_lon is not None:
        result["use_browser_location"] = True
        return {"name": "Your Location", "lat": browser_lat, "lon": browser_lon}

    result["use_browser_location"] = True
    return None


def _gazetteer_lookup(name: str):
    """Case-insensitive gazetteer lookup with partial matching."""
    name_low = name.lower().strip()
    # Exact match
    if name_low in _GAZETTEER:
        lat, lon = _GAZETTEER[name_low]
        return {"name": name_low.title(), "lat": lat, "lon": lon}
    # Partial match (startswith)
    for city, (lat, lon) in _GAZETTEER.items():
        if city.startswith(name_low) or name_low.startswith(city):
            return {"name": city.title(), "lat": lat, "lon": lon}
    return None


# ---------------------------------------------------------------------------
# Human-readable summary of what was extracted (for chat reply prefix)
# ---------------------------------------------------------------------------

def describe_intent(intent: dict) -> str:
    """Return a short human-readable description of the parsed intent."""
    parts = []
    loc = intent.get("location")
    if loc:
        parts.append(f"📍 Location: **{loc['name']}** ({loc['lat']:.3f}°, {loc['lon']:.3f}°)")
    elif intent.get("use_browser_location"):
        parts.append("📍 Location: **your current position** (from browser)")
    else:
        parts.append("📍 Location: *not resolved – using (0°, 0°)*")

    parts.append(f"⏱ Time window: **{intent['time_hours']:.0f} hours**")
    if intent.get("band_filter"):
        parts.append(f"📻 Band filter: **{intent['band_filter']}-band**")
    if intent.get("agency_filter"):
        parts.append(f"🏢 Agency filter: **{intent['agency_filter']}**")
    if intent["min_elevation"] != 10.0:
        parts.append(f"🔭 Min elevation: **{intent['min_elevation']}°**")
    return "\n".join(parts)
