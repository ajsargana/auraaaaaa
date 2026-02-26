"""
Earth Observation Satellite Database Manager

Manages EO satellite metadata including sensor specifications,
swath widths, and operational parameters.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class EOSatelliteDatabase:
    """
    Database for Earth Observation satellite specifications
    """

    def __init__(self, db_file='eo_satellites.json'):
        self.db_file = Path(db_file)
        self.satellites = {}
        self.load_database()

    def load_database(self):
        """Load EO satellite database from JSON file"""
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r') as f:
                    self.satellites = json.load(f)
                logger.info(f"✅ Loaded {len(self.satellites)} EO satellite configurations")
            except Exception as e:
                logger.error(f"Error loading EO database: {e}")
                self.satellites = {}
        else:
            logger.warning(f"EO database file not found: {self.db_file}")
            self.satellites = {}

    def save_database(self):
        """Save EO satellite database to JSON file"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.satellites, f, indent=2)
            logger.info(f"💾 Saved {len(self.satellites)} EO satellite configurations")
        except Exception as e:
            logger.error(f"Error saving EO database: {e}")

    def get_satellite(self, norad_id: int) -> Optional[Dict]:
        """Get EO satellite configuration by NORAD ID"""
        norad_str = str(norad_id)
        return self.satellites.get(norad_str)

    def is_eo_satellite(self, norad_id: int) -> bool:
        """Check if satellite is an Earth Observation satellite"""
        return str(norad_id) in self.satellites

    def get_all_eo_satellites(self) -> Dict:
        """Get all EO satellite configurations"""
        return self.satellites

    def add_satellite(self, norad_id: int, config: Dict):
        """Add or update EO satellite configuration"""
        norad_str = str(norad_id)
        self.satellites[norad_str] = config
        self.save_database()

    def get_by_constellation(self, constellation: str) -> List[Dict]:
        """Get all satellites in a constellation"""
        results = []
        for norad_id, config in self.satellites.items():
            if config.get('constellation', '').lower() == constellation.lower():
                config['norad_id'] = int(norad_id)
                results.append(config)
        return results

    def get_by_sensor_type(self, sensor_type: str) -> List[Dict]:
        """Get all satellites with specific sensor type"""
        results = []
        for norad_id, config in self.satellites.items():
            if config.get('sensor_type', '').lower() == sensor_type.lower():
                config['norad_id'] = int(norad_id)
                results.append(config)
        return results

    def initialize_default_satellites(self):
        """Initialize database with well-known EO satellites"""
        default_satellites = {
            # Landsat Program
            "39084": {
                "name": "LANDSAT 8",
                "constellation": "Landsat",
                "operator": "NASA/USGS",
                "sensor_type": "optical",
                "spatial_res_m": 15,
                "swath_km": 185,
                "altitude_km": 705,
                "off_nadir_deg": 0,
                "data_access": "open",
                "tasking": False,
                "url": "https://landsat.gsfc.nasa.gov/"
            },
            "49260": {
                "name": "LANDSAT 9",
                "constellation": "Landsat",
                "operator": "NASA/USGS",
                "sensor_type": "optical",
                "spatial_res_m": 15,
                "swath_km": 185,
                "altitude_km": 705,
                "off_nadir_deg": 0,
                "data_access": "open",
                "tasking": False,
                "url": "https://landsat.gsfc.nasa.gov/"
            },

            # Sentinel-2 (Optical)
            "40697": {
                "name": "SENTINEL-2A",
                "constellation": "Sentinel-2",
                "operator": "ESA",
                "sensor_type": "optical",
                "spatial_res_m": 10,
                "swath_km": 290,
                "altitude_km": 786,
                "off_nadir_deg": 0,
                "data_access": "open",
                "tasking": False,
                "url": "https://sentinel.esa.int/web/sentinel/missions/sentinel-2"
            },
            "42063": {
                "name": "SENTINEL-2B",
                "constellation": "Sentinel-2",
                "operator": "ESA",
                "sensor_type": "optical",
                "spatial_res_m": 10,
                "swath_km": 290,
                "altitude_km": 786,
                "off_nadir_deg": 0,
                "data_access": "open",
                "tasking": False,
                "url": "https://sentinel.esa.int/web/sentinel/missions/sentinel-2"
            },

            # Sentinel-1 (SAR - all weather)
            "39634": {
                "name": "SENTINEL-1A",
                "constellation": "Sentinel-1",
                "operator": "ESA",
                "sensor_type": "SAR",
                "spatial_res_m": 5,
                "swath_km": 250,
                "altitude_km": 693,
                "off_nadir_deg": 0,
                "data_access": "open",
                "tasking": False,
                "url": "https://sentinel.esa.int/web/sentinel/missions/sentinel-1"
            },
            "41456": {
                "name": "SENTINEL-1B",
                "constellation": "Sentinel-1",
                "operator": "ESA",
                "sensor_type": "SAR",
                "spatial_res_m": 5,
                "swath_km": 250,
                "altitude_km": 693,
                "off_nadir_deg": 0,
                "data_access": "open",
                "tasking": False,
                "url": "https://sentinel.esa.int/web/sentinel/missions/sentinel-1"
            },

            # Sentinel-3 (Ocean/Land)
            "41335": {
                "name": "SENTINEL-3A",
                "constellation": "Sentinel-3",
                "operator": "ESA",
                "sensor_type": "optical",
                "spatial_res_m": 300,
                "swath_km": 1270,
                "altitude_km": 814,
                "off_nadir_deg": 0,
                "data_access": "open",
                "tasking": False,
                "url": "https://sentinel.esa.int/web/sentinel/missions/sentinel-3"
            },
            "43437": {
                "name": "SENTINEL-3B",
                "constellation": "Sentinel-3",
                "operator": "ESA",
                "sensor_type": "optical",
                "spatial_res_m": 300,
                "swath_km": 1270,
                "altitude_km": 814,
                "off_nadir_deg": 0,
                "data_access": "open",
                "tasking": False,
                "url": "https://sentinel.esa.int/web/sentinel/missions/sentinel-3"
            },

            # Planet Labs (Dove constellation - representative samples)
            "40016": {
                "name": "FLOCK 1",
                "constellation": "Planet",
                "operator": "Planet Labs",
                "sensor_type": "optical",
                "spatial_res_m": 3,
                "swath_km": 24,
                "altitude_km": 475,
                "off_nadir_deg": 25,
                "data_access": "commercial",
                "tasking": True,
                "url": "https://www.planet.com/"
            },

            # SPOT (High resolution commercial)
            "40053": {
                "name": "SPOT 7",
                "constellation": "SPOT",
                "operator": "Airbus",
                "sensor_type": "optical",
                "spatial_res_m": 1.5,
                "swath_km": 60,
                "altitude_km": 694,
                "off_nadir_deg": 30,
                "data_access": "commercial",
                "tasking": True,
                "url": "https://www.airbus.com/space/earth-observation.html"
            },

            # WorldView (Very high resolution commercial)
            "35946": {
                "name": "WORLDVIEW-2",
                "constellation": "WorldView",
                "operator": "Maxar",
                "sensor_type": "optical",
                "spatial_res_m": 0.46,
                "swath_km": 16.4,
                "altitude_km": 770,
                "off_nadir_deg": 45,
                "data_access": "commercial",
                "tasking": True,
                "url": "https://www.maxar.com/"
            },
            "40115": {
                "name": "WORLDVIEW-3",
                "constellation": "WorldView",
                "operator": "Maxar",
                "sensor_type": "optical",
                "spatial_res_m": 0.31,
                "swath_km": 13.1,
                "altitude_km": 617,
                "off_nadir_deg": 45,
                "data_access": "commercial",
                "tasking": True,
                "url": "https://www.maxar.com/"
            },

            # Terra & Aqua (MODIS - wide swath)
            "25994": {
                "name": "TERRA",
                "constellation": "Terra",
                "operator": "NASA",
                "sensor_type": "optical",
                "spatial_res_m": 250,
                "swath_km": 2330,
                "altitude_km": 705,
                "off_nadir_deg": 0,
                "data_access": "open",
                "tasking": False,
                "url": "https://terra.nasa.gov/"
            },
            "27424": {
                "name": "AQUA",
                "constellation": "Aqua",
                "operator": "NASA",
                "sensor_type": "optical",
                "spatial_res_m": 250,
                "swath_km": 2330,
                "altitude_km": 705,
                "off_nadir_deg": 0,
                "data_access": "open",
                "tasking": False,
                "url": "https://aqua.nasa.gov/"
            },

            # NOAA Weather Satellites (AVHRR)
            "33591": {
                "name": "NOAA 18",
                "constellation": "NOAA",
                "operator": "NOAA",
                "sensor_type": "optical",
                "spatial_res_m": 1100,
                "swath_km": 2900,
                "altitude_km": 854,
                "off_nadir_deg": 0,
                "data_access": "open",
                "tasking": False,
                "url": "https://www.noaa.gov/"
            },
            "28654": {
                "name": "NOAA 19",
                "constellation": "NOAA",
                "operator": "NOAA",
                "sensor_type": "optical",
                "spatial_res_m": 1100,
                "swath_km": 2900,
                "altitude_km": 870,
                "off_nadir_deg": 0,
                "data_access": "open",
                "tasking": False,
                "url": "https://www.noaa.gov/"
            },

            # Pleiades (Very high resolution)
            "37745": {
                "name": "PLEIADES 1A",
                "constellation": "Pleiades",
                "operator": "Airbus",
                "sensor_type": "optical",
                "spatial_res_m": 0.5,
                "swath_km": 20,
                "altitude_km": 694,
                "off_nadir_deg": 40,
                "data_access": "commercial",
                "tasking": True,
                "url": "https://www.airbus.com/space/earth-observation.html"
            },
            "38012": {
                "name": "PLEIADES 1B",
                "constellation": "Pleiades",
                "operator": "Airbus",
                "sensor_type": "optical",
                "spatial_res_m": 0.5,
                "swath_km": 20,
                "altitude_km": 694,
                "off_nadir_deg": 40,
                "data_access": "commercial",
                "tasking": True,
                "url": "https://www.airbus.com/space/earth-observation.html"
            },

            # ICESAT-2 (Laser altimetry)
            "43613": {
                "name": "ICESAT-2",
                "constellation": "ICESat",
                "operator": "NASA",
                "sensor_type": "lidar",
                "spatial_res_m": 70,
                "swath_km": 7,
                "altitude_km": 496,
                "off_nadir_deg": 0,
                "data_access": "open",
                "tasking": False,
                "url": "https://icesat-2.gsfc.nasa.gov/"
            }
        }

        self.satellites = default_satellites
        self.save_database()
        logger.info(f"✅ Initialized {len(default_satellites)} default EO satellites")

        return len(default_satellites)
