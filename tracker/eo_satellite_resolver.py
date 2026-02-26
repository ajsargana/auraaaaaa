"""
EO Satellite Resolver
=====================
Maps a parsed EO pass intent (from core.eo_pass_nlu) to a list of candidate
(norad_id, metadata_dict) tuples for pass prediction.

Resolution priority:
  1. specific_satellite  → fuzzy TLE-name match
  2. sensor_type filter  → EarthObservationSatellites + keyword scan + EOSatelliteDatabase
  3. constellation       → TLE name prefix scan
  4. use_case            → expand to sensor_types → run Step 2 for each
  5. Fallback            → all NORAD IDs in EarthObservationSatellites DB

Returns up to MAX_CANDIDATES candidates.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

MAX_CANDIDATES = 200  # cap – spatial index is fast so large candidate sets are fine

# ---------------------------------------------------------------------------
# Sensor → TLE name keyword fragments
# Used for satellite_manager TLE-name scan (fallback when FOV DB is incomplete)
# ---------------------------------------------------------------------------
_SENSOR_TLE_KEYWORDS: dict[str, list[str]] = {
    "SAR":           ["SENTINEL-1", "RADARSAT", "TERRASAR", "TANDEM-X",
                      "COSMO-SKYMED", "ALOS", "RISAT", "ICEYE", "CAPELLA",
                      "UMBRA", "PAZ", "SMAP", "GAOFEN-3", "GAOFEN-12", "YAOGAN"],
    "optical":       ["WORLDVIEW", "GEOEYE", "PLEIADES", "SKYSAT", "DOVE",
                      "FLOCK", "BLACKSKY", "SPOT-6", "SPOT-7", "CARBONITE",
                      "GAOFEN-2", "GAOFEN-4", "GAOFEN-7", "CARTOSAT",
                      "KOMPSAT", "DEIMOS", "KAZEOSAT-1", "VNREDSAT",
                      "GOKTURK", "ALSAT", "THEOS", "DUBAISAT", "ZIYUAN"],
    "multispectral": ["SENTINEL-2", "LANDSAT", "RAPIDEYE", "RESOURCESAT",
                      "HUANJING", "CBERS", "HODOYOSHI", "LAPAN", "KAZEOSAT-2"],
    "thermal":       ["MODIS", "VIIRS", "NOAA", "SUOMI", "TERRA", "AQUA",
                      "SENTINEL-3", "GOES", "METOP"],
    "hyperspectral": ["PRISMA", "DESIS", "HYPERION", "GOSAT", "IBUKI"],
    "lidar":         ["ICESAT", "GEDI", "SARAL", "JASON"],
    "weather":       ["SENTINEL-5P", "GPM", "SMOS", "OCEANSAT", "HAIYANG",
                      "METOP", "NOAA-20"],
}

# ---------------------------------------------------------------------------
# Constellation → TLE name prefixes
# ---------------------------------------------------------------------------
_CONSTELLATION_TLE_PREFIXES: dict[str, list[str]] = {
    "Planet Labs":          ["DOVE", "FLOCK", "SKYSAT", "PLANETSCOPE"],
    "Sentinel":             ["SENTINEL-"],
    "WorldView":            ["WORLDVIEW", "GEOEYE"],
    "Landsat":              ["LANDSAT"],
    "MODIS":                ["TERRA", "AQUA"],
    "RADARSAT Constellation": ["RADARSAT CONSTELLATION", "RCM"],
    "COSMO-SkyMed":         ["COSMO-SKYMED", "CSK"],
    "ICEYE":                ["ICEYE"],
    "Capella":              ["CAPELLA"],
    "Umbra":                ["UMBRA"],
    "PAZ":                  ["PAZ"],
}

# ---------------------------------------------------------------------------
# Unified metadata builder
# ---------------------------------------------------------------------------
def _build_metadata(norad_id: int, fov_data: Optional[dict],
                    eo_db_entry: Optional[dict]) -> dict:
    """Merge FOV data + EO database entry into a unified metadata dict."""
    meta = {
        "norad_id":        norad_id,
        "name":            None,
        "sensor_type":     "optical",
        "swath_km":        None,
        "resolution_m":    None,
        "constellation":   None,
        "agency":          None,
        "use_cases":       [],
        "color":           "#94a3b8",
        "icon":            "🛰️",
        "altitude_km":     600,
        "off_nadir_deg":   0,       # agile pointing (0 = nadir-only pushbroom)
        "daylight_required": False,
    }

    # Populate from FOV data (highest accuracy for swath geometry)
    if fov_data:
        meta["name"]       = fov_data.get("name")
        meta["sensor_type"] = fov_data.get("sensor_type", "optical")
        meta["swath_km"]   = fov_data.get("default_swath")
        meta["agency"]     = fov_data.get("country")
        meta["altitude_km"] = fov_data.get("altitude_km", 600)

    # Overlay from EO database (has use-cases, resolution, constellation)
    if eo_db_entry:
        if not meta["name"]:
            meta["name"] = eo_db_entry.get("name")
        meta["sensor_type"]    = eo_db_entry.get("sensor_type", meta["sensor_type"])
        meta["resolution_m"]   = eo_db_entry.get("resolution_m") or eo_db_entry.get("spatial_res_m")
        meta["constellation"]  = eo_db_entry.get("constellation")
        meta["agency"]         = eo_db_entry.get("agency") or eo_db_entry.get("operator") or meta["agency"]
        meta["use_cases"]      = eo_db_entry.get("use_cases", [])
        meta["off_nadir_deg"]  = eo_db_entry.get("off_nadir_deg", 0) or 0
        if eo_db_entry.get("swath_km"):
            meta["swath_km"]   = eo_db_entry["swath_km"]
        elif eo_db_entry.get("swath_width_km"):
            meta["swath_km"]   = eo_db_entry["swath_width_km"]

    # Derived fields
    st = meta["sensor_type"]
    meta["daylight_required"] = st in ("optical", "multispectral")
    _apply_sensor_theme(meta)

    return meta


_SENSOR_THEMES = {
    "SAR":           {"color": "#00b4d8", "icon": "📡"},
    "optical":       {"color": "#52b788", "icon": "📷"},
    "thermal":       {"color": "#f4a261", "icon": "🌡️"},
    "multispectral": {"color": "#9b5de5", "icon": "🌈"},
    "hyperspectral": {"color": "#c77dff", "icon": "🔬"},
    "lidar":         {"color": "#48cae4", "icon": "💡"},
    "weather":       {"color": "#4ecdc4", "icon": "🌤️"},
}

def _apply_sensor_theme(meta: dict) -> None:
    theme = _SENSOR_THEMES.get(meta["sensor_type"], {})
    meta["color"] = theme.get("color", "#94a3b8")
    meta["icon"]  = theme.get("icon",  "🛰️")


# ---------------------------------------------------------------------------
# Fuzzy TLE name matcher (for specific_satellite lookup)
# ---------------------------------------------------------------------------
def _tokenize(name: str) -> set:
    return set(re.sub(r"[^a-z0-9]", " ", name.lower()).split())

def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def _fuzzy_find_norad(canonical: str, satellite_manager, threshold: float = 0.35):
    """
    Return list of NORAD IDs whose TLE name is fuzzy-similar to `canonical`.
    """
    tokens = _tokenize(canonical)
    # Also handle aliases (MODIS = TERRA + AQUA, VIIRS = SUOMI NPP + NOAA-20)
    aliases = {
        "MODIS":  ["TERRA", "AQUA"],
        "VIIRS":  ["SUOMI NPP", "NOAA-20"],
        "LANDSAT": ["LANDSAT 8", "LANDSAT 9"],
    }
    # If canonical is an alias key, expand
    targets = aliases.get(canonical.upper(), [canonical])

    matches = []
    for target in targets:
        target_tokens = _tokenize(target)
        for norad_id, sat in satellite_manager.satellites.items():
            sat_tokens = _tokenize(sat.get("name", ""))
            score = _jaccard(target_tokens, sat_tokens)
            if score >= threshold:
                matches.append(int(norad_id))

    return list(set(matches))


# ---------------------------------------------------------------------------
# Main resolver
# ---------------------------------------------------------------------------

def resolve_satellites(
    intent: dict,
    satellite_manager,
    fov_db,           # EarthObservationSatellites instance (tracker.satellite_fov_data)
    eo_database,      # EOSatelliteDatabase instance (may be None)
) -> list[dict]:
    """
    Resolve the NLU intent to a list of candidate metadata dicts.

    Parameters
    ----------
    intent           : dict from extract_eo_pass_intent()
    satellite_manager: SatelliteDataManager (has .satellites {norad_id: ...})
    fov_db           : EarthObservationSatellites (has .satellites {norad_id: ...})
    eo_database      : EOSatelliteDatabase (has .get_by_sensor_type() etc.) or None

    Returns
    -------
    List[dict]  – up to MAX_CANDIDATES candidates, each with unified metadata.
    """
    candidates: list[dict] = []
    seen_norad: set[int] = set()

    def _add(norad_id: int, inferred_sensor: str = None) -> None:
        """Add a candidate if not already in list and within cap.

        inferred_sensor: the sensor type that triggered this add (from TLE keyword
        scan). If the satellite has no FOV/EO DB entry, use this as the sensor type
        rather than the default "optical".
        """
        if len(candidates) >= MAX_CANDIDATES:
            return
        if norad_id in seen_norad:
            return
        # Verify satellite is actually loaded in TLE cache
        if int(norad_id) not in satellite_manager.satellites and \
           str(norad_id) not in satellite_manager.satellites:
            return
        seen_norad.add(norad_id)
        fov_data   = fov_db.satellites.get(norad_id)
        eo_entry   = _get_eo_db_entry(norad_id, eo_database)
        meta = _build_metadata(norad_id, fov_data, eo_entry)
        # If sensor type came only from TLE keyword scan (no DB entry), propagate it
        if inferred_sensor and not fov_data and not eo_entry:
            meta["sensor_type"] = inferred_sensor
            _apply_sensor_theme(meta)
        if not meta["name"]:
            # Fall back to TLE name
            sat = satellite_manager.satellites.get(int(norad_id)) or \
                  satellite_manager.satellites.get(str(norad_id))
            if sat:
                meta["name"] = sat.get("name", f"SAT-{norad_id}")
        candidates.append(meta)

    def _get_eo_db_entry(norad_id: int, eo_db) -> Optional[dict]:
        if eo_db is None:
            return None
        entry = (eo_db.satellites.get(str(norad_id)) or
                 eo_db.satellites.get(int(norad_id)))
        return entry

    # ── Step 1: specific satellite ───────────────────────────────────────
    specific = intent.get("specific_satellite")
    if specific:
        matched = _fuzzy_find_norad(specific, satellite_manager)
        for norad in matched:
            _add(norad)
        if candidates:
            logger.info(f"[Resolver] specific_satellite='{specific}' → {len(candidates)} match(es)")
            return candidates

    # ── Step 2: sensor_type filter ───────────────────────────────────────
    sensor_type = intent.get("sensor_type")
    sensor_types_list = intent.get("sensor_types", [])
    if sensor_type and sensor_type not in sensor_types_list:
        sensor_types_list = [sensor_type] + sensor_types_list

    if sensor_types_list:
        for st in sensor_types_list:
            # 2a. Scan EarthObservationSatellites FOV DB
            for norad_id, fov_data in fov_db.satellites.items():
                if fov_data.get("sensor_type", "").lower() == st.lower():
                    _add(int(norad_id))

            # 2b. Scan EOSatelliteDatabase
            if eo_database:
                try:
                    eo_matches = eo_database.get_by_sensor_type(st)
                    for entry in eo_matches:
                        nid = entry.get("norad_id") or entry.get("id")
                        if nid:
                            _add(int(nid))
                except Exception as e:
                    logger.debug(f"EODatabase sensor scan failed: {e}")

            # 2c. TLE name keyword scan
            keywords = _SENSOR_TLE_KEYWORDS.get(st, [])
            if keywords:
                for norad_id, sat in satellite_manager.satellites.items():
                    name = sat.get("name", "").upper()
                    if any(kw in name for kw in keywords):
                        _add(int(norad_id), inferred_sensor=st)

    # ── Step 3: constellation filter ────────────────────────────────────
    constellation = intent.get("constellation")
    if constellation and len(candidates) < MAX_CANDIDATES:
        prefixes = _CONSTELLATION_TLE_PREFIXES.get(constellation, [constellation.upper()])
        for norad_id, sat in satellite_manager.satellites.items():
            name = sat.get("name", "").upper()
            if any(name.startswith(p) or p in name for p in prefixes):
                _add(int(norad_id))
        # Also check EOSatelliteDatabase
        if eo_database:
            try:
                eo_matches = eo_database.get_by_constellation(constellation)
                for entry in eo_matches:
                    nid = entry.get("norad_id") or entry.get("id")
                    if nid:
                        _add(int(nid))
            except Exception as e:
                logger.debug(f"EODatabase constellation scan failed: {e}")

    # ── Step 5: fallback – all EO (FOV DB + full TLE keyword scan + SAR DB) ─
    if not candidates:
        logger.info("[Resolver] No sensor/constellation filter – scanning all EO sources")
        # 5a. FOV database (78 entries, 40+ in live TLE)
        for norad_id in fov_db.satellites:
            _add(int(norad_id))
        # 5b. Full TLE name keyword scan across ALL sensor types (~140 satellites)
        all_keywords = []
        for kws in _SENSOR_TLE_KEYWORDS.values():
            all_keywords.extend(kws)
        for norad_id, sat in satellite_manager.satellites.items():
            name = sat.get("name", "").upper()
            if any(kw in name for kw in all_keywords):
                _add(int(norad_id))
        # 5c. SAR satellite database
        try:
            from tracker.sar_satellite_db import SAR_SATELLITES
            for norad_id in SAR_SATELLITES:
                _add(int(norad_id))
        except ImportError:
            pass

    logger.info(f"[Resolver] Returning {len(candidates)} candidates "
                f"(sensor={sensor_types_list}, const={constellation})")
    return candidates
