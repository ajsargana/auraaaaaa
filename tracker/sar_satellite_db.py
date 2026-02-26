"""
SAR Satellite Database
======================
Comprehensive database of Synthetic Aperture Radar (SAR) satellites
with NORAD IDs, sensor specs, orbital characteristics, and scoring weights.

Used by the SAR Pass Prediction Pipeline to:
 1. Filter the live TLE data to SAR-only satellites
 2. Provide sensor metadata for pass quality scoring
 3. Support NLU sensor-type matching (band, mode, agency queries)
"""

# ---------------------------------------------------------------------------
# SAR_SATELLITES – keyed by NORAD catalogue number (int)
# ---------------------------------------------------------------------------
SAR_SATELLITES = {
    # ── ESA Copernicus Sentinel-1 ─────────────────────────────────────────
    39634: {
        "name": "SENTINEL-1A",
        "constellation": "Sentinel-1",
        "agency": "ESA",
        "country": "Europe",
        "band": "C",
        "frequency_ghz": 5.405,
        "wavelength_cm": 5.55,
        "polarisation": ["VV", "VH", "HH", "HV"],
        "modes": {
            "IW":  {"swath_km": 250, "resolution_m": 5,   "look_angle_deg": (29, 46)},
            "EW":  {"swath_km": 400, "resolution_m": 20,  "look_angle_deg": (19, 47)},
            "SM":  {"swath_km": 80,  "resolution_m": 5,   "look_angle_deg": (20, 45)},
            "WV":  {"swath_km": 20,  "resolution_m": 5,   "look_angle_deg": (23, 36)},
        },
        "default_mode": "IW",
        "repeat_cycle_days": 12,
        "altitude_km": 693,
        "inclination_deg": 98.18,
        "status": "active",
        "launch_date": "2014-04-03",
        "tle_name_fragment": "SENTINEL-1A",
        "color": "#00b4d8",
        "icon": "📡",
        "use_cases": ["flood mapping", "deforestation", "ice monitoring", "ship detection"],
    },
    44943: {
        "name": "SENTINEL-1C",
        "constellation": "Sentinel-1",
        "agency": "ESA",
        "country": "Europe",
        "band": "C",
        "frequency_ghz": 5.405,
        "wavelength_cm": 5.55,
        "polarisation": ["VV", "VH", "HH", "HV"],
        "modes": {
            "IW":  {"swath_km": 250, "resolution_m": 5,   "look_angle_deg": (29, 46)},
            "EW":  {"swath_km": 400, "resolution_m": 20,  "look_angle_deg": (19, 47)},
            "SM":  {"swath_km": 80,  "resolution_m": 5,   "look_angle_deg": (20, 45)},
        },
        "default_mode": "IW",
        "repeat_cycle_days": 12,
        "altitude_km": 693,
        "inclination_deg": 98.18,
        "status": "active",
        "launch_date": "2024-12-05",
        "tle_name_fragment": "SENTINEL-1C",
        "color": "#0096c7",
        "icon": "📡",
        "use_cases": ["flood mapping", "deforestation", "ice monitoring"],
    },

    # ── MDA RADARSAT ──────────────────────────────────────────────────────
    32382: {
        "name": "RADARSAT-2",
        "constellation": "RADARSAT",
        "agency": "CSA / MDA",
        "country": "Canada",
        "band": "C",
        "frequency_ghz": 5.405,
        "wavelength_cm": 5.55,
        "polarisation": ["HH", "HV", "VV", "VH", "compact"],
        "modes": {
            "Fine":            {"swath_km": 50,   "resolution_m": 8,   "look_angle_deg": (20, 49)},
            "Standard":        {"swath_km": 100,  "resolution_m": 25,  "look_angle_deg": (20, 49)},
            "Wide":            {"swath_km": 150,  "resolution_m": 30,  "look_angle_deg": (20, 45)},
            "ScanSAR Narrow":  {"swath_km": 300,  "resolution_m": 50,  "look_angle_deg": (20, 46)},
            "ScanSAR Wide":    {"swath_km": 500,  "resolution_m": 100, "look_angle_deg": (20, 49)},
            "Ultra-Fine":      {"swath_km": 20,   "resolution_m": 3,   "look_angle_deg": (20, 49)},
            "Multi-Look Fine": {"swath_km": 50,   "resolution_m": 8,   "look_angle_deg": (20, 49)},
        },
        "default_mode": "Standard",
        "repeat_cycle_days": 24,
        "altitude_km": 798,
        "inclination_deg": 98.6,
        "status": "active",
        "launch_date": "2007-12-14",
        "tle_name_fragment": "RADARSAT-2",
        "color": "#ff6b35",
        "icon": "🛰️",
        "use_cases": ["maritime surveillance", "disaster management", "agriculture"],
    },
    43014: {
        "name": "RADARSAT Constellation-1 (RCM-1)",
        "constellation": "RCM",
        "agency": "CSA",
        "country": "Canada",
        "band": "C",
        "frequency_ghz": 5.405,
        "wavelength_cm": 5.55,
        "polarisation": ["compact", "full"],
        "modes": {
            "Low Resolution":   {"swath_km": 500, "resolution_m": 100, "look_angle_deg": (19, 54)},
            "Medium Resolution": {"swath_km": 350, "resolution_m": 50,  "look_angle_deg": (19, 54)},
            "High Resolution":  {"swath_km": 125, "resolution_m": 16,  "look_angle_deg": (19, 54)},
            "Very High Res":    {"swath_km": 30,  "resolution_m": 3,   "look_angle_deg": (19, 54)},
            "Ship Detection":   {"swath_km": 350, "resolution_m": 50,  "look_angle_deg": (19, 54)},
        },
        "default_mode": "Medium Resolution",
        "repeat_cycle_days": 12,
        "altitude_km": 592,
        "inclination_deg": 97.74,
        "status": "active",
        "launch_date": "2019-06-12",
        "tle_name_fragment": "RCM-1",
        "color": "#f77f00",
        "icon": "🛰️",
        "use_cases": ["maritime", "ice mapping", "ecosystem monitoring"],
    },
    43015: {
        "name": "RADARSAT Constellation-2 (RCM-2)",
        "constellation": "RCM",
        "agency": "CSA",
        "country": "Canada",
        "band": "C",
        "frequency_ghz": 5.405,
        "wavelength_cm": 5.55,
        "polarisation": ["compact", "full"],
        "modes": {
            "Medium Resolution": {"swath_km": 350, "resolution_m": 50, "look_angle_deg": (19, 54)},
            "High Resolution":   {"swath_km": 125, "resolution_m": 16, "look_angle_deg": (19, 54)},
        },
        "default_mode": "Medium Resolution",
        "repeat_cycle_days": 12,
        "altitude_km": 592,
        "inclination_deg": 97.74,
        "status": "active",
        "launch_date": "2019-06-12",
        "tle_name_fragment": "RCM-2",
        "color": "#fcbf49",
        "icon": "🛰️",
        "use_cases": ["maritime", "ice mapping"],
    },
    43016: {
        "name": "RADARSAT Constellation-3 (RCM-3)",
        "constellation": "RCM",
        "agency": "CSA",
        "country": "Canada",
        "band": "C",
        "frequency_ghz": 5.405,
        "wavelength_cm": 5.55,
        "polarisation": ["compact", "full"],
        "modes": {
            "Medium Resolution": {"swath_km": 350, "resolution_m": 50, "look_angle_deg": (19, 54)},
            "High Resolution":   {"swath_km": 125, "resolution_m": 16, "look_angle_deg": (19, 54)},
        },
        "default_mode": "Medium Resolution",
        "repeat_cycle_days": 12,
        "altitude_km": 592,
        "inclination_deg": 97.74,
        "status": "active",
        "launch_date": "2019-06-12",
        "tle_name_fragment": "RCM-3",
        "color": "#eae2b7",
        "icon": "🛰️",
        "use_cases": ["maritime", "ice mapping"],
    },

    # ── DLR TerraSAR-X / TanDEM-X ─────────────────────────────────────────
    31698: {
        "name": "TERRASAR-X",
        "constellation": "TerraSAR-X",
        "agency": "DLR / Airbus",
        "country": "Germany",
        "band": "X",
        "frequency_ghz": 9.65,
        "wavelength_cm": 3.1,
        "polarisation": ["HH", "VV", "HV", "VH"],
        "modes": {
            "SpotLight":      {"swath_km": 10,  "resolution_m": 1,   "look_angle_deg": (20, 55)},
            "HighRes SpotL":  {"swath_km": 5,   "resolution_m": 0.25,"look_angle_deg": (20, 55)},
            "StripMap":       {"swath_km": 30,  "resolution_m": 3,   "look_angle_deg": (20, 45)},
            "ScanSAR":        {"swath_km": 100, "resolution_m": 16,  "look_angle_deg": (20, 45)},
        },
        "default_mode": "StripMap",
        "repeat_cycle_days": 11,
        "altitude_km": 514,
        "inclination_deg": 97.44,
        "status": "active",
        "launch_date": "2007-06-15",
        "tle_name_fragment": "TERRASAR-X",
        "color": "#e63946",
        "icon": "📡",
        "use_cases": ["urban mapping", "infrastructure monitoring", "DEM generation"],
    },
    37387: {
        "name": "TANDEM-X",
        "constellation": "TerraSAR-X",
        "agency": "DLR / Airbus",
        "country": "Germany",
        "band": "X",
        "frequency_ghz": 9.65,
        "wavelength_cm": 3.1,
        "polarisation": ["HH", "VV"],
        "modes": {
            "StripMap": {"swath_km": 30, "resolution_m": 3, "look_angle_deg": (20, 45)},
            "SpotLight": {"swath_km": 10, "resolution_m": 1, "look_angle_deg": (20, 55)},
        },
        "default_mode": "StripMap",
        "repeat_cycle_days": 11,
        "altitude_km": 514,
        "inclination_deg": 97.44,
        "status": "active",
        "launch_date": "2010-06-21",
        "tle_name_fragment": "TANDEM-X",
        "color": "#f4a261",
        "icon": "📡",
        "use_cases": ["DEM generation", "bistatic imaging", "InSAR"],
    },

    # ── PAZ (Spanish) ─────────────────────────────────────────────────────
    43215: {
        "name": "PAZ",
        "constellation": "PAZ",
        "agency": "Hisdesat / Indra",
        "country": "Spain",
        "band": "X",
        "frequency_ghz": 9.65,
        "wavelength_cm": 3.1,
        "polarisation": ["HH", "VV", "HV"],
        "modes": {
            "SpotLight": {"swath_km": 10, "resolution_m": 1, "look_angle_deg": (20, 55)},
            "StripMap":  {"swath_km": 30, "resolution_m": 3, "look_angle_deg": (20, 45)},
            "ScanSAR":   {"swath_km": 100,"resolution_m": 16,"look_angle_deg": (20, 45)},
        },
        "default_mode": "StripMap",
        "repeat_cycle_days": 11,
        "altitude_km": 514,
        "inclination_deg": 97.44,
        "status": "active",
        "launch_date": "2018-02-22",
        "tle_name_fragment": "PAZ",
        "color": "#a8dadc",
        "icon": "📡",
        "use_cases": ["surveillance", "urban monitoring"],
    },

    # ── ASI COSMO-SkyMed ──────────────────────────────────────────────────
    31598: {
        "name": "COSMO-SKYMED 1",
        "constellation": "COSMO-SkyMed",
        "agency": "ASI",
        "country": "Italy",
        "band": "X",
        "frequency_ghz": 9.6,
        "wavelength_cm": 3.1,
        "polarisation": ["HH", "VV", "HV", "VH"],
        "modes": {
            "SpotLight-2": {"swath_km": 10, "resolution_m": 1, "look_angle_deg": (20, 60)},
            "HImage":       {"swath_km": 40, "resolution_m": 3, "look_angle_deg": (20, 60)},
            "WideRegion":   {"swath_km": 100,"resolution_m": 16,"look_angle_deg": (20, 60)},
            "HugeRegion":   {"swath_km": 200,"resolution_m": 100,"look_angle_deg": (20,60)},
        },
        "default_mode": "HImage",
        "repeat_cycle_days": 16,
        "altitude_km": 619,
        "inclination_deg": 97.86,
        "status": "active",
        "launch_date": "2007-06-08",
        "tle_name_fragment": "COSMO-SKYMED 1",
        "color": "#2a9d8f",
        "icon": "📡",
        "use_cases": ["disaster response", "defense", "land subsidence"],
    },
    33412: {
        "name": "COSMO-SKYMED 2",
        "constellation": "COSMO-SkyMed",
        "agency": "ASI",
        "country": "Italy",
        "band": "X",
        "frequency_ghz": 9.6,
        "wavelength_cm": 3.1,
        "polarisation": ["HH", "VV", "HV", "VH"],
        "modes": {
            "SpotLight-2": {"swath_km": 10, "resolution_m": 1,  "look_angle_deg": (20, 60)},
            "HImage":       {"swath_km": 40, "resolution_m": 3,  "look_angle_deg": (20, 60)},
            "WideRegion":   {"swath_km": 100,"resolution_m": 16, "look_angle_deg": (20, 60)},
        },
        "default_mode": "HImage",
        "repeat_cycle_days": 16,
        "altitude_km": 619,
        "inclination_deg": 97.86,
        "status": "active",
        "launch_date": "2007-12-09",
        "tle_name_fragment": "COSMO-SKYMED 2",
        "color": "#264653",
        "icon": "📡",
        "use_cases": ["disaster response", "defense"],
    },
    35771: {
        "name": "COSMO-SKYMED 3",
        "constellation": "COSMO-SkyMed",
        "agency": "ASI",
        "country": "Italy",
        "band": "X",
        "frequency_ghz": 9.6,
        "wavelength_cm": 3.1,
        "polarisation": ["HH", "VV", "HV", "VH"],
        "modes": {
            "HImage":     {"swath_km": 40, "resolution_m": 3,  "look_angle_deg": (20, 60)},
            "WideRegion": {"swath_km": 100,"resolution_m": 16, "look_angle_deg": (20, 60)},
        },
        "default_mode": "HImage",
        "repeat_cycle_days": 16,
        "altitude_km": 619,
        "inclination_deg": 97.86,
        "status": "active",
        "launch_date": "2008-10-25",
        "tle_name_fragment": "COSMO-SKYMED 3",
        "color": "#e9c46a",
        "icon": "📡",
        "use_cases": ["disaster response", "land subsidence"],
    },
    36599: {
        "name": "COSMO-SKYMED 4",
        "constellation": "COSMO-SkyMed",
        "agency": "ASI",
        "country": "Italy",
        "band": "X",
        "frequency_ghz": 9.6,
        "wavelength_cm": 3.1,
        "polarisation": ["HH", "VV", "HV", "VH"],
        "modes": {
            "HImage":     {"swath_km": 40, "resolution_m": 3, "look_angle_deg": (20, 60)},
            "WideRegion": {"swath_km": 100,"resolution_m": 16,"look_angle_deg": (20, 60)},
        },
        "default_mode": "HImage",
        "repeat_cycle_days": 16,
        "altitude_km": 619,
        "inclination_deg": 97.86,
        "status": "active",
        "launch_date": "2010-11-05",
        "tle_name_fragment": "COSMO-SKYMED 4",
        "color": "#f4a261",
        "icon": "📡",
        "use_cases": ["disaster response", "defense"],
    },
    49771: {
        "name": "COSMO-SKYMED SG 1",
        "constellation": "COSMO-SkyMed SG",
        "agency": "ASI",
        "country": "Italy",
        "band": "X",
        "frequency_ghz": 9.6,
        "wavelength_cm": 3.1,
        "polarisation": ["quad-pol"],
        "modes": {
            "Ping Pong":  {"swath_km": 30,  "resolution_m": 10, "look_angle_deg": (20, 45)},
            "SpotLight":  {"swath_km": 10,  "resolution_m": 0.5,"look_angle_deg": (20, 60)},
            "StripMap":   {"swath_km": 40,  "resolution_m": 3,  "look_angle_deg": (20, 60)},
            "ScanSAR":    {"swath_km": 200, "resolution_m": 30, "look_angle_deg": (20, 45)},
        },
        "default_mode": "StripMap",
        "repeat_cycle_days": 16,
        "altitude_km": 619,
        "inclination_deg": 97.86,
        "status": "active",
        "launch_date": "2019-12-18",
        "tle_name_fragment": "COSMO-SKYMED SG",
        "color": "#06d6a0",
        "icon": "📡",
        "use_cases": ["sub-meter mapping", "InSAR", "defense"],
    },

    # ── JAXA ALOS-2 ───────────────────────────────────────────────────────
    39766: {
        "name": "ALOS-2",
        "constellation": "ALOS",
        "agency": "JAXA",
        "country": "Japan",
        "band": "L",
        "frequency_ghz": 1.2575,
        "wavelength_cm": 23.6,
        "polarisation": ["HH", "HV", "VH", "VV", "compact"],
        "modes": {
            "SpotLight":    {"swath_km": 25,  "resolution_m": 1,  "look_angle_deg": (8, 70)},
            "Ultra-Fine":   {"swath_km": 50,  "resolution_m": 3,  "look_angle_deg": (8, 70)},
            "High-Sensitive":{"swath_km": 50, "resolution_m": 6,  "look_angle_deg": (8, 70)},
            "Fine":         {"swath_km": 70,  "resolution_m": 10, "look_angle_deg": (8, 70)},
            "ScanSAR":      {"swath_km": 350, "resolution_m": 100,"look_angle_deg": (8, 70)},
            "Wide ScanSAR": {"swath_km": 490, "resolution_m": 60, "look_angle_deg": (8, 70)},
        },
        "default_mode": "Fine",
        "repeat_cycle_days": 14,
        "altitude_km": 628,
        "inclination_deg": 97.9,
        "status": "active",
        "launch_date": "2014-05-24",
        "tle_name_fragment": "ALOS-2",
        "color": "#118ab2",
        "icon": "📡",
        "use_cases": ["forest monitoring", "disaster", "InSAR subsidence", "vegetation"],
    },

    # ── ISRO RISAT ────────────────────────────────────────────────────────
    37387: {   # RISAT-1 (placeholder – check NORAD)
        "name": "RISAT-1",
        "constellation": "RISAT",
        "agency": "ISRO",
        "country": "India",
        "band": "C",
        "frequency_ghz": 5.35,
        "wavelength_cm": 5.6,
        "polarisation": ["HH", "HV", "VV", "VH"],
        "modes": {
            "Fine Resolution StripMap": {"swath_km": 30,  "resolution_m": 3,  "look_angle_deg": (12, 55)},
            "Medium Resolution":        {"swath_km": 115, "resolution_m": 25, "look_angle_deg": (12, 55)},
            "Coarse Resolution":        {"swath_km": 223, "resolution_m": 50, "look_angle_deg": (12, 55)},
        },
        "default_mode": "Medium Resolution",
        "repeat_cycle_days": 25,
        "altitude_km": 536,
        "inclination_deg": 97.55,
        "status": "degraded",
        "launch_date": "2012-04-26",
        "tle_name_fragment": "RISAT-1",
        "color": "#ff9f1c",
        "icon": "📡",
        "use_cases": ["flood", "agriculture", "defense"],
    },

    # ── ICEYE (commercial SAR constellation) ─────────────────────────────
    43800: {
        "name": "ICEYE-X2",
        "constellation": "ICEYE",
        "agency": "ICEYE",
        "country": "Finland",
        "band": "X",
        "frequency_ghz": 9.65,
        "wavelength_cm": 3.1,
        "polarisation": ["VV"],
        "modes": {
            "SpotLight": {"swath_km": 5,  "resolution_m": 0.5,"look_angle_deg": (15, 35)},
            "StripMap":  {"swath_km": 30, "resolution_m": 3,  "look_angle_deg": (15, 35)},
            "ScanSAR":   {"swath_km": 100,"resolution_m": 15, "look_angle_deg": (15, 35)},
        },
        "default_mode": "StripMap",
        "repeat_cycle_days": 1,
        "altitude_km": 570,
        "inclination_deg": 97.69,
        "status": "active",
        "launch_date": "2019-01-11",
        "tle_name_fragment": "ICEYE-X",
        "color": "#7209b7",
        "icon": "📡",
        "use_cases": ["rapid revisit", "maritime", "flood", "disaster"],
    },

    # ── Capella Space ────────────────────────────────────────────────────
    45609: {
        "name": "CAPELLA-2",
        "constellation": "Capella",
        "agency": "Capella Space",
        "country": "USA",
        "band": "X",
        "frequency_ghz": 9.65,
        "wavelength_cm": 3.1,
        "polarisation": ["HH"],
        "modes": {
            "SpotLight": {"swath_km": 5,  "resolution_m": 0.5,"look_angle_deg": (20, 50)},
            "StripMap":  {"swath_km": 25, "resolution_m": 1.2,"look_angle_deg": (20, 50)},
            "Sliding Spotlight": {"swath_km": 10,"resolution_m": 0.35,"look_angle_deg":(20,50)},
        },
        "default_mode": "StripMap",
        "repeat_cycle_days": 1,
        "altitude_km": 525,
        "inclination_deg": 97.4,
        "status": "active",
        "launch_date": "2020-08-31",
        "tle_name_fragment": "CAPELLA",
        "color": "#f72585",
        "icon": "📡",
        "use_cases": ["sub-meter imaging", "change detection", "maritime"],
    },

    # ── Umbra ─────────────────────────────────────────────────────────────
    50985: {
        "name": "UMBRA-04",
        "constellation": "Umbra",
        "agency": "Umbra Lab",
        "country": "USA",
        "band": "X",
        "frequency_ghz": 9.65,
        "wavelength_cm": 3.1,
        "polarisation": ["VV"],
        "modes": {
            "SpotLight":  {"swath_km": 5,  "resolution_m": 0.25,"look_angle_deg": (20, 55)},
            "StripMap":   {"swath_km": 20, "resolution_m": 1.0, "look_angle_deg": (20, 55)},
        },
        "default_mode": "SpotLight",
        "repeat_cycle_days": 1,
        "altitude_km": 525,
        "inclination_deg": 97.4,
        "status": "active",
        "launch_date": "2022-06-01",
        "tle_name_fragment": "UMBRA",
        "color": "#3d405b",
        "icon": "📡",
        "use_cases": ["very high-res surveillance", "infrastructure", "ships"],
    },
}

# ---------------------------------------------------------------------------
# TLE name fragment → NORAD lookup  (built from SAR_SATELLITES)
# ---------------------------------------------------------------------------
SAR_TLE_FRAGMENTS = {
    v["tle_name_fragment"].upper(): k
    for k, v in SAR_SATELLITES.items()
}

# Common SAR-related keyword patterns for NLU matching
SAR_KEYWORDS = [
    "sar", "synthetic aperture radar", "radar satellite",
    "sentinel-1", "sentinel 1", "radarsat", "terrasar", "tandem-x",
    "cosmo-skymed", "alos", "alos-2", "palsar", "risat",
    "iceye", "capella", "umbra", "paz",
    "c-band", "x-band", "l-band", "s-band",
    "sar pass", "radar pass", "sar satellite pass",
    "which sar", "what sar", "sar coverage",
]

# Band filter aliases used in NLU
BAND_ALIASES = {
    "c": "C", "c-band": "C", "c band": "C",
    "x": "X", "x-band": "X", "x band": "X",
    "l": "L", "l-band": "L", "l band": "L",
    "s": "S", "s-band": "S", "s band": "S",
    "ku": "Ku", "ku-band": "Ku",
}


def get_all_sar_norad_ids():
    """Return list of all SAR satellite NORAD IDs."""
    return list(SAR_SATELLITES.keys())


def get_sar_info(norad_id):
    """Return SAR metadata for a given NORAD ID, or None."""
    return SAR_SATELLITES.get(norad_id)


def get_sar_norad_by_tle_name(tle_name: str):
    """
    Match a TLE name to a SAR NORAD ID using fragment matching.
    Returns the NORAD ID (int) or None.
    """
    tle_upper = tle_name.upper().strip()
    # Exact fragment match first
    for fragment, norad_id in SAR_TLE_FRAGMENTS.items():
        if fragment in tle_upper or tle_upper in fragment:
            return norad_id
    return None


def filter_by_band(norad_ids, band: str):
    """Filter a list of NORAD IDs to only those matching the SAR band."""
    band_upper = BAND_ALIASES.get(band.lower(), band.upper())
    return [nid for nid in norad_ids if SAR_SATELLITES.get(nid, {}).get("band") == band_upper]


def filter_by_agency(norad_ids, agency: str):
    """Filter NORAD IDs by agency keyword (case-insensitive substring)."""
    kw = agency.lower()
    return [nid for nid in norad_ids if kw in SAR_SATELLITES.get(nid, {}).get("agency", "").lower()]


def get_sar_summary(norad_id):
    """Return a human-readable one-liner for a SAR satellite."""
    info = SAR_SATELLITES.get(norad_id)
    if not info:
        return f"NORAD {norad_id}"
    mode = info["modes"].get(info["default_mode"], {})
    return (
        f"{info['name']} ({info['band']}-band, {info['agency']}) — "
        f"swath {mode.get('swath_km','?')} km, "
        f"res {mode.get('resolution_m','?')} m"
    )
