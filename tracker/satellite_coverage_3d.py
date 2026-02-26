"""
3D Globe-Accurate Satellite Coverage Calculator

Uses proper geodesic calculations to create swaths that look correct
on a 3D globe, not just flat maps.

Key: Calculate perpendicular offsets using spherical geometry at each point.
"""

import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from skyfield.api import load, wgs84
from geographiclib.geodesic import Geodesic

logger = logging.getLogger(__name__)


class GlobeAccurateCoverageCalculator:
    """
    Calculate satellite coverage using geodesic geometry
    Ensures consistent swath width on 3D globe
    """

    def __init__(self, satellite_manager, eo_database):
        self.satellite_manager = satellite_manager
        self.eo_database = eo_database
        self.ts = load.timescale()

        # Use WGS84 ellipsoid for accurate geodesic calculations
        self.geod = Geodesic.WGS84

        # Load ephemeris for solar calculations
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
        Calculate coverage swath using proper geodesic geometry for 3D globe
        """
        eo_config = self.eo_database.get_satellite(norad_id)
        if not eo_config:
            return None

        if norad_id not in self.satellite_manager.satellites:
            return None

        try:
            sat_data = self.satellite_manager.satellites[norad_id]
            satellite_obj = sat_data['satellite_obj']
            swath_km = eo_config.get('swath_km', 100)
            sensor_type = eo_config.get('sensor_type', 'optical')

            logger.info(f"📊 3D-accurate coverage for {sat_data['name']}: swath={swath_km}km")

            # Calculate satellite positions
            now = datetime.now(timezone.utc)
            start_time = now - timedelta(hours=hours_past)
            end_time = now + timedelta(hours=hours_future)

            positions = self._get_satellite_positions(
                satellite_obj, start_time, end_time, interval_minutes,
                swath_km, sensor_type
            )

            if len(positions) < 2:
                return None

            # Create geodesic swath corridor
            coverage_data = self._create_geodesic_swath(positions, swath_km)

            coverage_data['norad_id'] = norad_id
            coverage_data['name'] = sat_data['name']
            coverage_data['swath_km'] = swath_km
            coverage_data['sensor_type'] = sensor_type
            coverage_data['spatial_res_m'] = eo_config.get('spatial_res_m', 0)
            coverage_data['constellation'] = eo_config.get('constellation', '')

            logger.info(f"✅ Generated 3D-accurate coverage swath")
            return coverage_data

        except Exception as e:
            logger.error(f"Error calculating coverage: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_satellite_positions(self, satellite_obj, start_time, end_time,
                                 step_minutes, swath_km, sensor_type):
        """Calculate satellite positions at regular intervals"""
        positions = []
        current_time = start_time

        while current_time <= end_time:
            t = self.ts.from_datetime(current_time)
            geocentric = satellite_obj.at(t)
            lat, lon = wgs84.latlon_of(geocentric)

            # Check daytime
            is_daytime = False
            if sensor_type == 'optical' and self.eph:
                is_daytime = self._is_daytime(lat.degrees, lon.degrees, current_time)
            elif sensor_type in ['SAR', 'lidar']:
                is_daytime = True

            positions.append({
                'timestamp': current_time,
                'lat': lat.degrees,
                'lon': lon.degrees,
                'swath_km': swath_km,
                'sensor_type': sensor_type,
                'daytime': is_daytime
            })

            current_time += timedelta(minutes=step_minutes)

        return positions

    def _create_geodesic_swath(self, positions: List[Dict], swath_km: float) -> Dict:
        """
        Create swath using TRUE geodesic perpendiculars

        Key insight: For each ground track point, calculate the azimuth (heading),
        then compute perpendicular offsets at azimuth±90° using geodesic lines.
        """
        if len(positions) < 2:
            return self._empty_result()

        half_swath_km = swath_km / 2.0 * 1000  # Convert to meters

        left_edge = []
        right_edge = []
        center_track = []

        # Calculate swath edges using geodesic perpendiculars
        for i in range(len(positions)):
            pos = positions[i]
            lat = pos['lat']
            lon = pos['lon']

            center_track.append([lon, lat])

            # Calculate forward azimuth (heading)
            if i == 0 and len(positions) > 1:
                # First point: use azimuth to next point
                line = self.geod.Inverse(lat, lon, positions[i+1]['lat'], positions[i+1]['lon'])
                azimuth = line['azi1']
            elif i == len(positions) - 1 and i > 0:
                # Last point: use azimuth from previous point
                line = self.geod.Inverse(positions[i-1]['lat'], positions[i-1]['lon'], lat, lon)
                azimuth = line['azi2']  # Forward azimuth at end point
            else:
                # Middle points: average azimuth
                line1 = self.geod.Inverse(positions[i-1]['lat'], positions[i-1]['lon'], lat, lon)
                line2 = self.geod.Inverse(lat, lon, positions[i+1]['lat'], positions[i+1]['lon'])
                azimuth = (line1['azi2'] + line2['azi1']) / 2.0

            # Calculate perpendicular points using geodesic Direct method
            # Left edge: azimuth - 90°
            left_point = self.geod.Direct(lat, lon, azimuth - 90, half_swath_km)
            left_edge.append([left_point['lon2'], left_point['lat2']])

            # Right edge: azimuth + 90°
            right_point = self.geod.Direct(lat, lon, azimuth + 90, half_swath_km)
            right_edge.append([right_point['lon2'], right_point['lat2']])

        # Create day/night segments
        day_polygons = self._create_illumination_segments(positions, left_edge, right_edge, True)
        night_polygons = self._create_illumination_segments(positions, left_edge, right_edge, False)

        # Create full coverage polygon
        full_polygon_coords = left_edge + list(reversed(right_edge)) + [left_edge[0]]

        return {
            'ground_track': center_track,
            'positions': [
                {
                    'time': p['timestamp'].isoformat(),
                    'lat': p['lat'],
                    'lon': p['lon']
                } for p in positions
            ],
            'polygons': [{'type': 'Polygon', 'coordinates': [full_polygon_coords]}],
            'day_polygons': day_polygons,
            'night_polygons': night_polygons
        }

    def _create_illumination_segments(self, positions: List[Dict],
                                     left_edge: List, right_edge: List,
                                     is_day: bool) -> List[Dict]:
        """Create polygons for continuous day or night segments"""
        polygons = []
        current_segment = []

        for i, pos in enumerate(positions):
            if pos['daytime'] == is_day:
                current_segment.append(i)
            else:
                # Illumination changed
                if len(current_segment) >= 2:
                    polygon = self._create_segment_polygon(
                        current_segment, left_edge, right_edge
                    )
                    if polygon:
                        polygons.append(polygon)
                current_segment = []

        # Handle last segment
        if len(current_segment) >= 2:
            polygon = self._create_segment_polygon(
                current_segment, left_edge, right_edge
            )
            if polygon:
                polygons.append(polygon)

        return polygons

    def _create_segment_polygon(self, indices: List[int],
                                left_edge: List, right_edge: List) -> Optional[Dict]:
        """Create polygon for a segment"""
        if len(indices) < 2:
            return None

        start_idx = indices[0]
        end_idx = indices[-1]

        # Get segment edges
        seg_left = left_edge[start_idx:end_idx+1]
        seg_right = right_edge[start_idx:end_idx+1]

        # Check for antimeridian crossing
        all_coords = seg_left + seg_right
        for i in range(1, len(all_coords)):
            if abs(all_coords[i][0] - all_coords[i-1][0]) > 180:
                # Skip segments crossing antimeridian
                return None

        # Create closed polygon
        coords = seg_left + list(reversed(seg_right)) + [seg_left[0]]

        return {
            'type': 'Polygon',
            'coordinates': [coords]
        }

    def _is_daytime(self, lat_degrees, lon_degrees, observation_time):
        """Determine if location is in daylight"""
        if not self.eph:
            return False

        try:
            location = self.earth + wgs84.latlon(lat_degrees, lon_degrees)
            t = self.ts.from_datetime(observation_time)
            astrometric = location.at(t).observe(self.sun)
            alt, az, distance = astrometric.apparent().altaz()
            return alt.degrees > 0
        except Exception as e:
            logger.warning(f"Error calculating solar position: {e}")
            return False

    def _empty_result(self):
        """Return empty result structure"""
        return {
            'ground_track': [],
            'positions': [],
            'polygons': [],
            'day_polygons': [],
            'night_polygons': []
        }

    def calculate_current_ground_swath(self, norad_id: int) -> Optional[Dict]:
        """Calculate current ground swath with geodesic accuracy"""
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

            # Calculate heading
            t_after = t + timedelta(seconds=30)
            geocentric_after = satellite_obj.at(self.ts.from_datetime(
                now + timedelta(seconds=30)
            ))
            lat_after, lon_after = wgs84.latlon_of(geocentric_after)

            line = self.geod.Inverse(lat.degrees, lon.degrees, lat_after.degrees, lon_after.degrees)
            heading = line['azi1']

            # Create swath rectangle
            polygon = self._create_geodesic_rectangle(
                lat.degrees, lon.degrees, swath_km, heading
            )

            # Check daytime
            is_daytime = False
            if sensor_type == 'optical' and self.eph:
                is_daytime = self._is_daytime(lat.degrees, lon.degrees, now)
            elif sensor_type in ['SAR', 'lidar']:
                is_daytime = True

            return {
                'norad_id': norad_id,
                'name': sat_data['name'],
                'center_lat': lat.degrees,
                'center_lon': lon.degrees,
                'swath_km': swath_km,
                'heading': heading,
                'daytime': is_daytime,
                'sensor_type': sensor_type,
                'polygon': polygon,
                'timestamp': now.isoformat()
            }

        except Exception as e:
            logger.error(f"Error calculating ground swath: {e}")
            return None

    def _create_geodesic_rectangle(self, lat: float, lon: float,
                                   swath_km: float, heading: float,
                                   length_km: float = 100) -> Dict:
        """
        Create swath rectangle using dense geodesic sampling
        for smooth curves on 3D globe
        """
        half_swath_m = swath_km / 2.0 * 1000
        half_length_m = length_km / 2.0 * 1000

        # Create rectangle with many intermediate points for smooth curves
        num_points = 20  # Increased for smoother curves
        corners = []

        # Front edge (perpendicular to heading)
        front = self.geod.Direct(lat, lon, heading, half_length_m)
        for i in range(num_points + 1):
            t = i / num_points - 0.5  # -0.5 to 0.5
            offset_m = t * swath_km * 1000
            edge_point = self.geod.Direct(front['lat2'], front['lon2'], heading + 90, offset_m)
            corners.append([edge_point['lon2'], edge_point['lat2']])

        # Right edge
        right_start = self.geod.Direct(lat, lon, heading + 90, half_swath_m)
        for i in range(1, num_points + 1):
            t = i / num_points  # 0 to 1
            offset_m = (t - 0.5) * length_km * 1000
            edge_point = self.geod.Direct(right_start['lat2'], right_start['lon2'], heading, offset_m)
            corners.append([edge_point['lon2'], edge_point['lat2']])

        # Back edge
        back = self.geod.Direct(lat, lon, heading + 180, half_length_m)
        for i in range(1, num_points + 1):
            t = 1 - i / num_points  # 1 to 0
            offset_m = (t - 0.5) * swath_km * 1000
            edge_point = self.geod.Direct(back['lat2'], back['lon2'], heading + 90, offset_m)
            corners.append([edge_point['lon2'], edge_point['lat2']])

        # Left edge
        left_start = self.geod.Direct(lat, lon, heading - 90, half_swath_m)
        for i in range(1, num_points):
            t = 1 - i / num_points  # 1 to 0
            offset_m = (t - 0.5) * length_km * 1000
            edge_point = self.geod.Direct(left_start['lat2'], left_start['lon2'], heading, offset_m)
            corners.append([edge_point['lon2'], edge_point['lat2']])

        # Close polygon
        corners.append(corners[0])

        return {'type': 'Polygon', 'coordinates': [corners]}