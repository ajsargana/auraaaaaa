"""
Satellite Coverage Calculator - Direct Implementation from eo-predictor

Uses the EXACT same approach as Development Seed's eo-predictor:
1. Calculate satellite positions at 5-minute intervals
2. Create LineString segments between consecutive points
3. Project to Web Mercator (EPSG:3395) for accurate distance buffering
4. Buffer by swath_km * 500 meters (half-width)
5. Project back to WGS84

This guarantees consistent, beautiful coverage swaths.
"""

import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from skyfield.api import load, wgs84
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point
import json

logger = logging.getLogger(__name__)


class EOPredictorCoverageCalculator:
    """
    Coverage calculator using eo-predictor's exact methodology
    """

    def __init__(self, satellite_manager, eo_database):
        self.satellite_manager = satellite_manager
        self.eo_database = eo_database
        self.ts = load.timescale()

        # Load ephemeris for daytime calculations
        try:
            self.eph = load('de421.bsp')
            self.earth = self.eph['earth']
            self.sun = self.eph['sun']
            logger.info("✅ Loaded ephemeris for solar calculations")
        except Exception as e:
            logger.warning(f"Could not load ephemeris: {e}")
            self.eph = None

    def calculate_coverage_swath(self, norad_id: int, hours_past: float = 1.0,
                                 hours_future: float = 1.0,
                                 interval_minutes: int = 2) -> Optional[Dict]:
        """
        Calculate coverage swath using eo-predictor's exact approach

        Args:
            norad_id: Satellite NORAD ID
            hours_past: Hours to look backward
            hours_future: Hours to look forward
            interval_minutes: Time step (default 2 minutes for smooth curves at poles)
        """
        eo_config = self.eo_database.get_satellite(norad_id)
        if not eo_config:
            logger.warning(f"Satellite {norad_id} not in EO database")
            return None

        if norad_id not in self.satellite_manager.satellites:
            logger.warning(f"Satellite {norad_id} not loaded")
            return None

        try:
            sat_data = self.satellite_manager.satellites[norad_id]
            satellite_obj = sat_data['satellite_obj']
            swath_km = eo_config.get('swath_km', 100)
            sensor_type = eo_config.get('sensor_type', 'optical')

            logger.info(f"📊 EO-Predictor method for {sat_data['name']}: swath={swath_km}km")

            # STEP 1: Calculate satellite positions (like eo-predictor)
            now = datetime.now(timezone.utc)
            start_time = now - timedelta(hours=hours_past)
            end_time = now + timedelta(hours=hours_future)

            positions = self._get_satellite_positions(
                satellite_obj, start_time, end_time, interval_minutes,
                swath_km, sensor_type
            )

            if len(positions) < 2:
                logger.warning("Not enough positions calculated")
                return None

            # STEP 2: Create LineString segments and check daytime
            path_segments = self._create_path_segments(positions)

            if not path_segments:
                logger.warning("No valid path segments created")
                return None

            # STEP 3: Convert to GeoDataFrame and buffer (eo-predictor's method)
            coverage_gdf = self._buffer_paths_to_polygons(path_segments, swath_km)

            # STEP 4: Convert to GeoJSON format for frontend
            coverage_data = self._convert_to_geojson(coverage_gdf, positions)

            coverage_data['norad_id'] = norad_id
            coverage_data['name'] = sat_data['name']
            coverage_data['swath_km'] = swath_km
            coverage_data['sensor_type'] = sensor_type
            coverage_data['spatial_res_m'] = eo_config.get('spatial_res_m', 0)
            coverage_data['constellation'] = eo_config.get('constellation', '')

            logger.info(f"✅ Generated coverage using eo-predictor method")
            return coverage_data

        except Exception as e:
            logger.error(f"Error calculating coverage: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_satellite_positions(self, satellite_obj, start_time, end_time,
                                 step_minutes, swath_km, sensor_type):
        """
        Calculate satellite positions at regular intervals
        (Exactly like eo-predictor's get_satellite_positions function)
        """
        positions = []
        current_time = start_time

        while current_time <= end_time:
            t = self.ts.from_datetime(current_time)
            geocentric = satellite_obj.at(t)
            lat, lon = wgs84.latlon_of(geocentric)

            positions.append({
                'timestamp': current_time,
                'coordinates': Point(lon.degrees, lat.degrees),
                'lat': lat.degrees,
                'lon': lon.degrees,
                'swath_km': swath_km,
                'sensor_type': sensor_type
            })

            current_time += timedelta(minutes=step_minutes)

        return positions

    def _create_path_segments(self, positions):
        """
        Create LineString segments between consecutive positions
        Handle antimeridian crossing properly by adjusting coordinates
        """
        path_segments = []

        for i in range(len(positions) - 1):
            pt0 = positions[i]['coordinates']
            pt1 = positions[i + 1]['coordinates']

            lon0 = pt0.x
            lon1 = pt1.x
            lat0 = pt0.y
            lat1 = pt1.y

            # Handle antimeridian crossing by adjusting lon1
            if abs(lon1 - lon0) > 180:
                # Crossing detected - adjust the second point
                if lon1 > lon0:
                    lon1 -= 360  # Wrap westward
                else:
                    lon1 += 360  # Wrap eastward

                # Create adjusted point
                pt1_adjusted = Point(lon1, lat1)
                line = LineString([pt0, pt1_adjusted])
            else:
                line = LineString([pt0, pt1])

            # Calculate daytime status for segment center
            center_lat = (lat0 + lat1) / 2
            center_lon = (lon0 + lon1) / 2
            middle_time = positions[i]['timestamp'] + (
                positions[i + 1]['timestamp'] - positions[i]['timestamp']
            ) / 2

            is_daytime = self._is_daytime(center_lat, center_lon, middle_time)

            path_segments.append({
                'start_time': positions[i]['timestamp'],
                'end_time': positions[i + 1]['timestamp'],
                'geometry': line,
                'swath_km': positions[i]['swath_km'],
                'sensor_type': positions[i]['sensor_type'],
                'is_daytime': is_daytime
            })

        return path_segments

    def _buffer_paths_to_polygons(self, path_segments, swath_km):
        """
        Buffer paths to create polygons using eo-predictor's EXACT method:
        1. Create GeoDataFrame with WGS84 (EPSG:4326)
        2. Project to Web Mercator (EPSG:3395) for accurate distance calculations
        3. Buffer by swath_km * 500 meters (half-width)
        4. Project back to WGS84

        This is THE KEY to getting beautiful, consistent coverage swaths!
        """
        # Create GeoDataFrame
        path_gdf = gpd.GeoDataFrame(path_segments, geometry='geometry', crs='EPSG:4326')

        # Project to Web Mercator (EPSG:3395) for accurate buffering
        path_gdf_proj = path_gdf.to_crs('EPSG:3395')

        # Buffer by half the swath width (in meters)
        # swath_km * 500 = half-width in meters
        path_gdf_proj['geometry'] = path_gdf_proj.apply(
            lambda row: row.geometry.buffer(row['swath_km'] * 500), axis=1
        )

        # Project back to WGS84
        path_gdf = path_gdf_proj.to_crs('EPSG:4326')

        return path_gdf

    def _convert_to_geojson(self, gdf, positions):
        """
        Convert GeoDataFrame to GeoJSON format for frontend visualization
        """
        # Extract ground track from positions with normalized longitudes
        ground_track = []
        for p in positions:
            lon = p['lon']
            # Normalize longitude to [-180, 180]
            while lon > 180:
                lon -= 360
            while lon < -180:
                lon += 360
            ground_track.append([lon, p['lat']])

        # Separate day and night polygons
        day_polygons = []
        night_polygons = []
        all_polygons = []

        for idx, row in gdf.iterrows():
            geom = row['geometry']

            # Convert to GeoJSON format
            if geom.is_empty:
                continue

            # Normalize coordinates to [-180, 180]
            coords_normalized = []
            for coord in geom.exterior.coords:
                lon = coord[0]
                lat = coord[1]
                # Normalize longitude to [-180, 180]
                while lon > 180:
                    lon -= 360
                while lon < -180:
                    lon += 360
                coords_normalized.append([lon, lat])

            polygon_geojson = {
                'type': 'Polygon',
                'coordinates': [coords_normalized]
            }

            all_polygons.append(polygon_geojson)

            if row['is_daytime']:
                day_polygons.append(polygon_geojson)
            else:
                night_polygons.append(polygon_geojson)

        return {
            'ground_track': ground_track,
            'positions': [
                {
                    'time': p['timestamp'].isoformat(),
                    'lat': p['lat'],
                    'lon': p['lon']
                } for p in positions
            ],
            'polygons': all_polygons,
            'day_polygons': day_polygons,
            'night_polygons': night_polygons
        }

    def _is_daytime(self, lat_degrees, lon_degrees, observation_time):
        """
        Determine if it's daytime at a given location and time
        (Exactly like eo-predictor's is_daytime function)
        """
        if not self.eph:
            return False

        try:
            # Create location on Earth's surface
            location = self.earth + wgs84.latlon(lat_degrees, lon_degrees)

            # Convert datetime to Skyfield time
            t = self.ts.from_datetime(observation_time)

            # Calculate solar position relative to the location
            astrometric = location.at(t).observe(self.sun)
            alt, az, distance = astrometric.apparent().altaz()

            # Return True if sun is above horizon (elevation > 0°)
            return alt.degrees > 0

        except Exception as e:
            logger.warning(f"Error calculating solar position: {e}")
            return False

    def calculate_current_ground_swath(self, norad_id: int) -> Optional[Dict]:
        """
        Calculate current ground swath (for animated visualization)
        """
        eo_config = self.eo_database.get_satellite(norad_id)
        if not eo_config or norad_id not in self.satellite_manager.satellites:
            return None

        try:
            sat_data = self.satellite_manager.satellites[norad_id]
            satellite_obj = sat_data['satellite_obj']
            swath_km = eo_config.get('swath_km', 100)
            sensor_type = eo_config.get('sensor_type', 'optical')

            # Get current position
            now = datetime.now(timezone.utc)
            t = self.ts.from_datetime(now)
            geocentric = satellite_obj.at(t)
            lat, lon = wgs84.latlon_of(geocentric)

            # Calculate positions for a short segment (2 minutes before/after)
            positions = []
            for delta_minutes in [-2, 0, 2]:
                time_point = now + timedelta(minutes=delta_minutes)
                t_point = self.ts.from_datetime(time_point)
                geocentric_point = satellite_obj.at(t_point)
                lat_point, lon_point = wgs84.latlon_of(geocentric_point)

                positions.append({
                    'timestamp': time_point,
                    'coordinates': Point(lon_point.degrees, lat_point.degrees),
                    'lat': lat_point.degrees,
                    'lon': lon_point.degrees,
                    'swath_km': swath_km,
                    'sensor_type': sensor_type
                })

            # Create path segments
            segments = self._create_path_segments(positions)

            if not segments:
                return None

            # Buffer to create swath
            gdf = self._buffer_paths_to_polygons(segments, swath_km)

            # Get first polygon
            if len(gdf) == 0:
                return None

            geom = gdf.iloc[0]['geometry']
            coords = [list(geom.exterior.coords)]

            is_daytime = self._is_daytime(lat.degrees, lon.degrees, now)

            return {
                'norad_id': norad_id,
                'name': sat_data['name'],
                'center_lat': lat.degrees,
                'center_lon': lon.degrees,
                'swath_km': swath_km,
                'daytime': is_daytime,
                'sensor_type': sensor_type,
                'polygon': {
                    'type': 'Polygon',
                    'coordinates': coords
                },
                'timestamp': now.isoformat()
            }

        except Exception as e:
            logger.error(f"Error calculating ground swath: {e}")
            return None
