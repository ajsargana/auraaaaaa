"""
Universal EO Pass NLU – Natural Language Understanding for any EO satellite pass query
=======================================================================================
Handles all sensor types: SAR, optical, thermal, multispectral, hyperspectral, lidar,
weather, and also specific-satellite / constellation / use-case queries.

Imports location + time utilities from core.sar_nlu to avoid duplication.

Returns intent dict:
{
  "is_eo_pass_query"  : bool,
  "is_sar_query"      : bool,          # backward-compat flag
  "sensor_type"       : str | None,    # "SAR"|"optical"|"thermal"|"multispectral"|
                                       #  "hyperspectral"|"lidar"|"weather"|None (=all EO)
  "specific_satellite": str | None,    # e.g. "LANDSAT-9", "SENTINEL-2A"
  "constellation"     : str | None,    # e.g. "Planet Labs", "Sentinel"
  "use_case"          : str | None,    # "flood"|"fire"|"agriculture"|...
  "location"          : {name, lat, lon} | None,
  "time_hours"        : float,         # default 48 h
  "min_elevation"     : float,         # default 10°
  "daylight_only"     : bool,          # auto-True for optical
  "resolution_tier"   : str | None,    # "sub-meter"|"medium"|"coarse"|None
  "raw_time_text"     : str | None,
  "use_browser_location": bool,
}
"""

import re
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Re-use shared utilities from sar_nlu (DRY – no duplicate code)
# ---------------------------------------------------------------------------
try:
    from core.sar_nlu import (
        _GAZETTEER, _TIME_PATTERNS, _SAR_PASS_PATTERNS,
        _extract_location,          # internal helper
    )
except ImportError:
    # Fallback: minimal stubs so the module can still load standalone
    _GAZETTEER = {}
    _TIME_PATTERNS = []
    _SAR_PASS_PATTERNS = []
    def _extract_location(low, blat, blon, result):   # noqa
        return None

# ---------------------------------------------------------------------------
# Pass-intent patterns (universal – all sensor types)
# ---------------------------------------------------------------------------
_EO_PASS_PATTERNS = list(_SAR_PASS_PATTERNS) + [
    r"\bsatellite.*over\b",
    r"\bover\b.*\bsatellite\b",
    r"\bwhich\s+satellite\b",
    r"\bwhat\s+satellite\b",
    r"\bwhen\s+(will|does|is)\b.*\bsat(ellite)?\b",
    r"\bnext\s+sat(ellite)?\b",
    r"\bsatellite.*pass(es|ing)?\b",
    r"\bimag(e|ery|ing)\b.*\bover\b",
    r"\bover\b.*\bimag(e|ery|ing)\b",
    r"\bcaptur(e|ing)\b.*\barea\b",
    r"\bsensor\b.*\bpass\b",
    r"\bfootprint\b",
    r"\bswath\b",
    r"\brevisit\b",
    r"\bacquisition\b",
    r"\boverfly\b",
    r"\bfly.*over\b",
]

# ---------------------------------------------------------------------------
# Sensor-type keyword groups
# ---------------------------------------------------------------------------
_SENSOR_PATTERNS: dict[str, list[str]] = {
    "SAR": [
        r"\bsar\b",
        r"synthetic\s+aperture\s+radar",
        r"radar\s+satellite",
        r"sentinel[\s\-]1[abc]?",
        r"\bradarsat\b",
        r"\bterrasar\b",
        r"\btandem[\s\-]x\b",
        r"\bcosmo[\s\-]skymed\b",
        r"\balos[\s\-]?2?\b",
        r"\bpalsar\b",
        r"\brisat\b",
        r"\biceye\b",
        r"\bcapella\s+sat",
        r"\bumbra\b",
        r"\bpaz\b",
        r"\bsmap\b",
        r"[clxs][\s\-]band\s+radar",
        r"sar\s+(pass|coverage|satellite|image)",
        r"(which|what|any)\s+sar",
        r"\bgaofen[\s\-]3\b",
        r"\bgaofen[\s\-]12\b",
        r"\byaogan\b",
    ],
    "optical": [
        r"\boptical\b",
        r"\bworldview[\s\-]?\d?\b",
        r"\bgeoeye\b",
        r"\bpleiades\b",
        r"\bskysat\b",
        r"\bdove\b",
        r"\bblacksky\b",
        r"\bcarbonite\b",
        r"\bgaofen[\s\-]2\b",
        r"\bgaofen[\s\-]4\b",
        r"\bgaofen[\s\-]7\b",
        r"\bspot[\s\-][67]\b",
        r"\bspott?ing\b",
        r"\bhigh[\s\-]?res(olution)?\s+(optical|image)",
        r"\bvisual\s+(image|imaging)\b",
        r"\bpanchromatic\b",
        r"\bpan\s+image\b",
        r"\bvhr\b",                 # Very High Resolution
        r"\bhr\b.*\bimage\b",
        r"\bsubmeter\b",
        r"\bsub[\s\-]meter\b",
        r"\bvnredsat\b",
        r"\bkazeosat[\s\-]1\b",
        r"\bgokturk\b",
        r"\bcartosat\b",
    ],
    "thermal": [
        r"\bthermal\b",
        r"\binfrared\b",
        r"\bir\s+image",
        r"\btirs\b",
        r"\beci\s+sensor\b",
        r"\blst\b",                 # Land Surface Temp
        r"\bfire\s+detect",
        r"\bheat\s+(detect|map|signature)\b",
        r"\bslstr\b",
        r"\bseviri\b",
        r"\bmodis\b",
        r"\bviirs\b",
        r"\bterra\b",
        r"\baqua\b",
        r"\bsuomi\b",
        r"\bnoaa[\s\-]?\d\b",
        r"\bgoes\b",
        r"\blst\b",
    ],
    "multispectral": [
        r"\bmultispectral\b",
        r"\bms\s+image\b",
        r"\bsentinel[\s\-]2[abc]?\b",
        r"\blandsat[\s\-]?[789]\b",
        r"\blandsat\b",
        r"\bndvi\b",
        r"\bnir\b",
        r"\bswir\b",
        r"\bvegetation\s+(index|image|map)\b",
        r"\bchlorophyll\b",
        r"\brap?ideye\b",
        r"\bhuanjing\b",
        r"\brecourcesat\b",
        r"\bresourcesat\b",
        r"\bhj[\s\-]?1[ab]\b",
        r"\bcbers\b",
        r"\bhodoyoshi\b",
        r"\blapan\b",
        r"\bkazeosat[\s\-]2\b",
        r"\bgaofen[\s\-]1\b",
        r"\bdeimos[\s\-]2\b",
    ],
    "hyperspectral": [
        r"\bhyperspectral\b",
        r"\bhsi\b",
        r"\bprisma\b",
        r"\bdesis\b",
        r"\bhyperion\b",
        r"\bgosat\b",
        r"\bibuki\b",
        r"\bochre\b",
        r"\bminerals?\s+mapping\b",
        r"\bcontaminants?\s+detect\b",
    ],
    "lidar": [
        r"\blidar\b",
        r"\bicesat[\s\-]?2?\b",
        r"\bgedi\b",
        r"\bsaral\b",
        r"\bjason[\s\-]3\b",
        r"\baltim(etry|eter)\b",
        r"\bbathymetry\b",
        r"\bcanopy\s+height\b",
        r"\bice\s+sheet\b",
    ],
    "weather": [
        r"\bweather\s+satellite\b",
        r"\bmeteorol\w+\s+satellite\b",
        r"\bsentinel[\s\-]5[p]?\b",
        r"\btropomi\b",
        r"\bgoes[\s\-]?\d*\b",
        r"\bnoaa[\s\-]?\d\d\b",
        r"\bmetop\b",
        r"\bsmos\b",
        r"\bgpm\b",
        r"\btrmm\b",
        r"\boceansat\b",
        r"\bhaiyang\b",
        r"\bscat(terometer)?\b",
        r"\bwind\s+(speed|sensor)\b",
        r"\bprecipitation\s+radar\b",
        r"\batmospher",
        r"\bozone\b",
        r"\bno2\b",
        r"\bair\s+quality\b",
    ],
}

# ---------------------------------------------------------------------------
# Use-case → sensor type routing
# ---------------------------------------------------------------------------
_USE_CASE_SENSOR_MAP: dict[str, list[str]] = {
    "flood":         ["SAR", "optical"],
    "fire":          ["thermal", "SAR"],
    "agriculture":   ["multispectral", "optical"],
    "deforestation": ["SAR", "multispectral"],
    "urban":         ["optical", "SAR"],
    "disaster":      ["SAR", "optical", "thermal"],
    "air_quality":   ["weather", "hyperspectral"],
    "ice":           ["SAR", "optical", "thermal"],
    "ocean":         ["optical", "weather", "SAR"],
    "coastline":     ["optical", "multispectral"],
    "mineral":       ["hyperspectral"],
    "elevation":     ["lidar"],
    "forest":        ["multispectral", "lidar", "SAR"],
    "crop":          ["multispectral", "optical"],
    "drought":       ["multispectral", "thermal"],
    "snow":          ["optical", "SAR", "multispectral"],
    "oil_spill":     ["SAR", "optical"],
    "shipping":      ["SAR", "optical"],
}

_USE_CASE_PATTERNS: dict[str, list[str]] = {
    "flood":         [r"\bflood(ing|s|ed)?\b", r"\binundation\b"],
    "fire":          [r"\bfir(e|es)\b", r"\bwildfires?\b", r"\bburn(ing|ed)?\b"],
    "agriculture":   [r"\bagricult\w+\b", r"\bfarm(ing|land)?\b", r"\bcrop(s|land)?\b"],
    "deforestation": [r"\bdeforest\w+\b", r"\btree\s+loss\b", r"\bclearing\b"],
    "urban":         [r"\burban\b", r"\bcity\s+growth\b", r"\bbuilt[\s\-]?up\b"],
    "disaster":      [r"\bdisaster\b", r"\bemergency\b", r"\bcrisis\b", r"\bcalamity\b"],
    "air_quality":   [r"\bair\s+quality\b", r"\bpollut\w+\b", r"\bsmog\b"],
    "ice":           [r"\bice[\s\-]?(sheet|cap|berg|field)?\b", r"\barctic\b", r"\bantarct\w+\b"],
    "ocean":         [r"\bocean\b", r"\bsea\s+(color|temp|surface)\b", r"\bmarine\b"],
    "coastline":     [r"\bcoast(al|line)?\b", r"\bshore(line)?\b"],
    "mineral":       [r"\bmineral\b", r"\bgeolog\w+\b", r"\bore\b"],
    "elevation":     [r"\belevation\b", r"\bdem\b", r"\bterrain\b"],
    "forest":        [r"\bforest\b", r"\bwoodland\b", r"\bcanopy\b"],
    "crop":          [r"\bcrop(s)?\b", r"\bharvest\b", r"\byield\b"],
    "drought":       [r"\bdrought\b", r"\bwater\s+stress\b"],
    "snow":          [r"\bsnow(fall|cover|melt)?\b", r"\bglacie\w+\b"],
    "oil_spill":     [r"\boil\s+spill\b", r"\bpetroleum\s+leak\b"],
    "shipping":      [r"\bship(ping|s)?\b", r"\bvessel\b", r"\bais\b"],
}

# ---------------------------------------------------------------------------
# Specific-satellite name patterns → canonical name
# ---------------------------------------------------------------------------
_SAT_NAME_PATTERNS: list[tuple[str, str]] = [
    # Landsat
    (r"\blandsat[\s\-]?9\b",          "LANDSAT-9"),
    (r"\blandsat[\s\-]?8\b",          "LANDSAT-8"),
    (r"\blandsat[\s\-]?7\b",          "LANDSAT-7"),
    (r"\blandsat[\s\-]?5\b",          "LANDSAT-5"),
    (r"\blandsat\b",                  "LANDSAT"),
    # Sentinel
    (r"\bsentinel[\s\-]?2[ac]\b",     "SENTINEL-2A"),
    (r"\bsentinel[\s\-]?2[b]\b",      "SENTINEL-2B"),
    (r"\bsentinel[\s\-]?2\b",         "SENTINEL-2"),
    (r"\bsentinel[\s\-]?1[ac]\b",     "SENTINEL-1A"),
    (r"\bsentinel[\s\-]?1[b]\b",      "SENTINEL-1B"),
    (r"\bsentinel[\s\-]?1\b",         "SENTINEL-1"),
    (r"\bsentinel[\s\-]?3[a]\b",      "SENTINEL-3A"),
    (r"\bsentinel[\s\-]?3[b]\b",      "SENTINEL-3B"),
    (r"\bsentinel[\s\-]?5p?\b",       "SENTINEL-5P"),
    # WorldView
    (r"\bworldview[\s\-]?4\b",        "WORLDVIEW-4"),
    (r"\bworldview[\s\-]?3\b",        "WORLDVIEW-3"),
    (r"\bworldview[\s\-]?2\b",        "WORLDVIEW-2"),
    (r"\bworldview[\s\-]?1\b",        "WORLDVIEW-1"),
    (r"\bworldview\b",                "WORLDVIEW"),
    # Terra/Aqua MODIS
    (r"\bterra\b",                    "TERRA"),
    (r"\baqua\b",                     "AQUA"),
    (r"\bmodis\b",                    "MODIS"),
    (r"\bviirs\b",                    "VIIRS"),
    (r"\bsuomi[\s\-]?npp\b",          "SUOMI NPP"),
    (r"\bnoaa[\s\-]?20\b",            "NOAA-20"),
    (r"\bnoaa[\s\-]?18\b",            "NOAA-18"),
    (r"\bnoaa[\s\-]?19\b",            "NOAA-19"),
    # Planet / SkySat
    (r"\bskysat[\s\-]?\w*\b",         "SKYSAT"),
    (r"\bdove\b",                     "DOVE"),
    (r"\bflock\b",                    "FLOCK"),
    # GeoEye / Pleiades
    (r"\bgeoeye[\s\-]?1\b",           "GEOEYE-1"),
    (r"\bpleiades[\s\-]?neo[\s\-]?\d", "PLEIADES-NEO"),
    (r"\bpleiades[\s\-]?1[ab]\b",     "PLEIADES-1"),
    (r"\bpleiades\b",                 "PLEIADES"),
    # SPOT
    (r"\bspot[\s\-]?7\b",             "SPOT-7"),
    (r"\bspot[\s\-]?6\b",             "SPOT-6"),
    # RADARSAT
    (r"\bradarsat[\s\-]?2\b",         "RADARSAT-2"),
    (r"\bradarsat[\s\-]?c\b",         "RADARSAT-CONSTELLATION"),
    (r"\bradarsat\b",                 "RADARSAT"),
    # TerraSAR-X / TanDEM-X
    (r"\bterrasar[\s\-]?x\b",        "TERRASAR-X"),
    (r"\btandem[\s\-]?x\b",           "TANDEM-X"),
    # COSMO-SkyMed
    (r"\bcosmo[\s\-]?skymed\b",       "COSMO-SKYMED"),
    # ALOS / PALSAR
    (r"\balos[\s\-]?2\b",             "ALOS-2"),
    (r"\balos\b",                     "ALOS"),
    # ICESat / GEDI
    (r"\bicesat[\s\-]?2\b",           "ICESAT-2"),
    (r"\bgedi\b",                     "GEDI"),
    # GOSAT
    (r"\bgosat\b",                    "GOSAT"),
    (r"\bibuki\b",                    "GOSAT"),
    # GPM
    (r"\bgpm\b",                      "GPM CORE"),
    # SMAP
    (r"\bsmap\b",                     "SMAP"),
    # SARAL
    (r"\bsaral\b",                    "SARAL"),
    # Jason-3
    (r"\bjason[\s\-]?3\b",            "JASON-3"),
    # Kompsat
    (r"\bkompsat[\s\-]?5\b",          "KOMPSAT-5"),
    (r"\bkompsat[\s\-]?3\b",          "KOMPSAT-3"),
    (r"\bkompsat[\s\-]?2\b",          "KOMPSAT-2"),
    # PRISMA
    (r"\bprisma\b",                   "PRISMA"),
    # ICEYE
    (r"\biceye\b",                    "ICEYE"),
    # Capella
    (r"\bcapella\b",                  "CAPELLA"),
    # Umbra
    (r"\bumbra\b",                    "UMBRA"),
]

# ---------------------------------------------------------------------------
# Constellation name patterns → canonical name
# ---------------------------------------------------------------------------
_CONSTELLATION_PATTERNS: list[tuple[str, str]] = [
    (r"\bplanet\s+labs?\b",           "Planet Labs"),
    (r"\bplanet\s+sat(ellites?)?\b",  "Planet Labs"),
    (r"\bplanetscope\b",              "Planet Labs"),
    (r"\bflock\b",                    "Planet Labs"),
    (r"\bdove\b",                     "Planet Labs"),
    (r"\bsentinel\b",                 "Sentinel"),
    (r"\bworldview\b",                "WorldView"),
    (r"\bdigitalglobe\b",             "WorldView"),
    (r"\bmaxar\b",                    "WorldView"),
    (r"\blandsat\b",                  "Landsat"),
    (r"\bmodis\b",                    "MODIS"),
    (r"\bradarsat[\s\-]?cons",        "RADARSAT Constellation"),
    (r"\bcosmo[\s\-]?skymed\b",       "COSMO-SkyMed"),
    (r"\biceye\b",                    "ICEYE"),
    (r"\bcapella\b",                  "Capella"),
    (r"\bumbra\b",                    "Umbra"),
    (r"\bpaz\b",                      "PAZ"),
]

# ---------------------------------------------------------------------------
# Resolution tier keywords
# ---------------------------------------------------------------------------
_RESOLUTION_PATTERNS: list[tuple[str, str]] = [
    (r"\bsub[\s\-]?met(er|re)\b",    "sub-meter"),
    (r"\bvhr\b",                      "sub-meter"),
    (r"\bvery\s+high\s+res",          "sub-meter"),
    (r"\b[<≤]?\s*1\s*m\b",           "sub-meter"),
    (r"\bmedium\s+res",               "medium"),
    (r"\bmr\b",                       "medium"),
    (r"\b(?:5|10|15|20|30)\s*m\s+res","medium"),
    (r"\bcoarse\b",                   "coarse"),
    (r"\blow\s+res",                  "coarse"),
    (r"\b250\s*m\b",                  "coarse"),
    (r"\b500\s*m\b",                  "coarse"),
    (r"\bkilometr",                   "coarse"),
]

# ---------------------------------------------------------------------------
# Core NLU function
# ---------------------------------------------------------------------------

def extract_eo_pass_intent(
    user_input: str,
    browser_lat: float = None,
    browser_lon: float = None,
) -> dict:
    """
    Parse user_input and return a structured universal EO pass query dict.

    Parameters
    ----------
    user_input   : raw chat message
    browser_lat  : latitude from browser GPS (or None)
    browser_lon  : longitude from browser GPS (or None)

    Returns
    -------
    dict  (see module docstring for full schema)
    """
    txt = user_input.strip()
    low = txt.lower()

    result = {
        "is_eo_pass_query":   False,
        "is_sar_query":       False,    # backward-compat
        "sensor_type":        None,
        "sensor_types":       [],       # multi-sensor (use-case routing)
        "specific_satellite": None,
        "constellation":      None,
        "use_case":           None,
        "location":           None,
        "time_hours":         48.0,
        "min_elevation":      10.0,
        "daylight_only":      False,
        "resolution_tier":    None,
        "raw_time_text":      None,
        "use_browser_location": False,
    }

    # ── 1. Detect any EO/pass intent ────────────────────────────────────
    pass_hit = any(re.search(p, low) for p in _EO_PASS_PATTERNS)

    # Also trigger on sensor keywords alone (e.g. "thermal satellite over X")
    sensor_hit = any(
        any(re.search(p, low) for p in patterns)
        for patterns in _SENSOR_PATTERNS.values()
    )

    use_case_hit = any(
        any(re.search(p, low) for p in patterns)
        for patterns in _USE_CASE_PATTERNS.values()
    )

    specific_sat_hit = any(re.search(p, low) for p, _ in _SAT_NAME_PATTERNS)

    if not (pass_hit or (sensor_hit and (
        re.search(r"\bsatellite\b", low) or
        re.search(r"\bpass(es)?\b", low) or
        re.search(r"\bover\b", low) or
        re.search(r"\bimage\b", low)
    )) or (use_case_hit and re.search(r"\bsatellite\b", low)) or specific_sat_hit):
        return result  # Not an EO pass query

    result["is_eo_pass_query"] = True

    # ── 2. Detect specific satellite name ────────────────────────────────
    for pattern, canonical in _SAT_NAME_PATTERNS:
        if re.search(pattern, low):
            result["specific_satellite"] = canonical
            break

    # ── 3. Detect sensor type ────────────────────────────────────────────
    detected_sensor = None
    for sensor_name, patterns in _SENSOR_PATTERNS.items():
        if any(re.search(p, low) for p in patterns):
            detected_sensor = sensor_name
            break   # first match wins (order = priority)

    result["sensor_type"] = detected_sensor

    # If SAR was detected, also set backward-compat flag
    if detected_sensor == "SAR":
        result["is_sar_query"] = True

    # ── 4. Detect constellation ──────────────────────────────────────────
    for pattern, canonical in _CONSTELLATION_PATTERNS:
        if re.search(pattern, low):
            result["constellation"] = canonical
            break

    # ── 5. Detect use-case and expand to sensor types ────────────────────
    for uc, patterns in _USE_CASE_PATTERNS.items():
        if any(re.search(p, low) for p in patterns):
            result["use_case"] = uc
            result["sensor_types"] = _USE_CASE_SENSOR_MAP.get(uc, [])
            # If no explicit sensor type, derive from use-case
            if not detected_sensor and result["sensor_types"]:
                result["sensor_type"] = result["sensor_types"][0]
            break

    # ── 6. Detect resolution tier ────────────────────────────────────────
    for pattern, tier in _RESOLUTION_PATTERNS:
        if re.search(pattern, low):
            result["resolution_tier"] = tier
            break

    # ── 7. Auto-set daylight_only ────────────────────────────────────────
    effective_sensor = result["sensor_type"]
    if effective_sensor in ("optical", "multispectral"):
        result["daylight_only"] = True
    if re.search(r"\bnigh?t\b|\bdark(ness)?\b|\bno[\s-]?light\b", low):
        result["daylight_only"] = False  # user explicitly wants night passes

    # ── 8. Extract location ──────────────────────────────────────────────
    result["location"] = _extract_location(low, browser_lat, browser_lon, result)

    # ── 9. Extract time window ───────────────────────────────────────────
    for pattern, converter in _TIME_PATTERNS:
        m = re.search(pattern, low)
        if m:
            try:
                hours = converter(m)
                if 1 <= hours <= 720:
                    result["time_hours"] = hours
                    result["raw_time_text"] = m.group(0)
            except Exception:
                pass
            break

    # ── 10. Extract min elevation ────────────────────────────────────────
    m = re.search(r"(\d+(?:\.\d+)?)\s*[°\s]?\s*(?:min(?:imum)?\s*)?elev(?:ation)?", low)
    if m:
        try:
            elev = float(m.group(1))
            if 0 <= elev <= 90:
                result["min_elevation"] = elev
        except Exception:
            pass

    return result


# ---------------------------------------------------------------------------
# Human-readable summary (for chat response header)
# ---------------------------------------------------------------------------
_SENSOR_LABELS = {
    "SAR":           "SAR / Radar",
    "optical":       "Optical",
    "thermal":       "Thermal Infrared",
    "multispectral": "Multispectral",
    "hyperspectral": "Hyperspectral",
    "lidar":         "LiDAR / Altimetry",
    "weather":       "Weather Sensor",
}


def describe_eo_intent(intent: dict) -> str:
    """Return a one-line human-readable description of the parsed intent."""
    parts = []

    if intent.get("specific_satellite"):
        parts.append(f"satellite: {intent['specific_satellite']}")
    elif intent.get("constellation"):
        parts.append(f"constellation: {intent['constellation']}")
    elif intent.get("sensor_type"):
        label = _SENSOR_LABELS.get(intent["sensor_type"], intent["sensor_type"])
        parts.append(f"sensor: {label}")
    else:
        parts.append("sensor: all EO")

    if intent.get("use_case"):
        parts.append(f"use-case: {intent['use_case']}")

    loc = intent.get("location")
    if loc:
        parts.append(f"location: {loc.get('name', 'custom')}")
    elif intent.get("use_browser_location"):
        parts.append("location: your position")

    parts.append(f"window: {intent.get('time_hours', 48):.0f} h")

    if intent.get("resolution_tier"):
        parts.append(f"resolution: {intent['resolution_tier']}")

    return " | ".join(parts)
