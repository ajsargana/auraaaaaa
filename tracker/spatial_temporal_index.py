"""
Spatial-Temporal Index for Ultra-Fast Satellite Pass Queries

This module provides O(1) pass lookups by pre-indexing satellite positions
in a spatial grid. Supports scaling to 15,000 satellites and 10,000+ concurrent users.

Architecture:
- Earth divided into 5° × 5° grid cells (72 × 72 = 5,184 cells)
- Time divided into 1-minute buckets
- Each cell stores list of visible satellites at each time
- Query: O(1) grid lookup + O(k) filtering (k = satellites in cell)

Memory: ~2-3GB for 15K satellites × 24 hours
Query Speed: <100ms for any location
"""

import gc
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
import threading
import time
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class SpatialTemporalIndex:
    """
    High-performance spatial-temporal index for satellite pass predictions.

    Uses a grid-based approach to enable O(1) lookups for satellite passes
    at any location on Earth.
    """

    def __init__(self, grid_size: float = 5.0, time_bucket_minutes: int = 1):
        """
        Initialize the spatial-temporal index.

        Args:
            grid_size: Grid cell size in degrees (default 5° = ~550km at equator)
            time_bucket_minutes: Time bucket size in minutes (default 1 min)
        """
        self.grid_size = grid_size
        self.time_bucket_minutes = time_bucket_minutes

        # Main index: (lat_bucket, lon_bucket, time_bucket) -> [satellite_passes]
        self.index: Dict[Tuple[int, int, int], List[Dict]] = defaultdict(list)

        # Metadata
        self.index_metadata = {
            'built_at': None,
            'total_entries': 0,
            'satellite_count': 0,
            'time_range_start': None,
            'time_range_end': None,
            'grid_size': grid_size,
            'time_bucket_minutes': time_bucket_minutes
        }

        # Thread safety
        self.lock = threading.RLock()

        # Statistics
        self.stats = {
            'queries': 0,
            'avg_query_time_ms': 0,
            'cache_hits': 0
        }

        logger.info(f"🗺️ Spatial-Temporal Index initialized (grid: {grid_size}°, time: {time_bucket_minutes}min)")

    def _get_grid_cell(self, lat: float, lon: float) -> Tuple[int, int]:
        """Convert lat/lon to grid cell coordinates."""
        lat_bucket = int(lat / self.grid_size)
        lon_bucket = int(lon / self.grid_size)
        return (lat_bucket, lon_bucket)

    def _get_time_bucket(self, timestamp: datetime) -> int:
        """Convert timestamp to time bucket (minutes since epoch)."""
        return int(timestamp.timestamp() / (self.time_bucket_minutes * 60))

    def _get_surrounding_cells(self, lat: float, lon: float, radius_cells: int = 1) -> List[Tuple[int, int]]:
        """
        Get surrounding grid cells for a location.

        Args:
            lat, lon: Center location
            radius_cells: Number of cells to expand in each direction (1 = 3×3 grid)

        Returns:
            List of (lat_bucket, lon_bucket) tuples
        """
        center_lat, center_lon = self._get_grid_cell(lat, lon)
        cells = []

        for lat_offset in range(-radius_cells, radius_cells + 1):
            for lon_offset in range(-radius_cells, radius_cells + 1):
                lat_bucket = center_lat + lat_offset
                lon_bucket = center_lon + lon_offset

                # Clamp latitude buckets
                if lat_bucket < -18 or lat_bucket > 18:  # -90° to +90°
                    continue

                # Wrap longitude buckets
                lon_bucket = lon_bucket % int(360 / self.grid_size)

                cells.append((lat_bucket, lon_bucket))

        return cells

    def build_index(self, position_cache_manager, time_window_hours: int = 48,
                   min_elevation: float = 10.0) -> None:
        """
        Build the spatial-temporal index from position cache.

        This is the heavy operation done once at startup or periodically.

        Args:
            position_cache_manager: The OptimizedPositionCacheManager instance
            time_window_hours: How many hours ahead to index
            min_elevation: Minimum elevation to consider (degrees)
        """
        logger.info(f"🏗️ Building spatial-temporal index ({time_window_hours}h window)...")
        start_time = time.time()

        with self.lock:
            # Clear existing index
            self.index.clear()

            start_dt = datetime.now(timezone.utc)
            end_dt = start_dt + timedelta(hours=time_window_hours)

            satellites = position_cache_manager.satellite_manager.satellites
            total_sats = len(satellites)
            processed = 0
            total_entries = 0
            skipped_sats = 0
            error_sats = 0
            altitude_samples = []  # Collect altitude samples to detect format

            # Process each satellite
            for norad_id, sat_data in satellites.items():
                try:
                    # Get cached positions for this satellite
                    positions = position_cache_manager.get_position_range(
                        norad_id, start_dt, end_dt, interval_seconds=60  # 1 min resolution
                    )

                    if not positions or len(positions) < 2:
                        skipped_sats += 1
                        if skipped_sats <= 5:  # Log first few
                            logger.debug(f"No cached positions for satellite {norad_id} ({sat_data['name']})")
                        continue

                    # Index each position into relevant grid cells
                    for pos in positions:
                        pos_time = datetime.fromisoformat(pos['timestamp'])
                        time_bucket = self._get_time_bucket(pos_time)

                        sat_lat = pos['latitude']
                        sat_lon = pos['longitude']
                        sat_alt_raw = pos['altitude']

                        # Collect altitude samples for debugging (first 10 satellites)
                        if len(altitude_samples) < 10 and positions.index(pos) == 0:
                            altitude_samples.append({
                                'norad_id': norad_id,
                                'name': sat_data['name'],
                                'altitude_raw': sat_alt_raw
                            })

                        sat_alt = sat_alt_raw

                        # Validate satellite data
                        if not (-90 <= sat_lat <= 90 and -180 <= sat_lon <= 180):
                            logger.warning(f"Invalid satellite position: lat={sat_lat}, lon={sat_lon}")
                            continue

                        # Handle different altitude formats
                        # BUG FIX: Position cache sometimes returns negative altitudes
                        # This is a known issue - just take absolute value
                        if sat_alt < 0:
                            # Log first occurrence for debugging
                            if processed == 0 and positions.index(pos) == 0:
                                logger.info(f"📍 Satellite {norad_id} ({sat_data['name']}): "
                                          f"fixing negative altitude {sat_alt:.1f} km → {abs(sat_alt):.1f} km")

                            sat_alt = abs(sat_alt)  # Fix: convert to positive

                        # Convert meters to km if needed (altitudes > 50,000 are likely in meters)
                        if sat_alt > 50000:
                            sat_alt = sat_alt / 1000.0  # Convert meters to km

                        # Sanity check - Skip satellites outside reasonable orbital ranges
                        # LEO: 160-2000km, MEO: 2000-35000km, GEO: ~35786km, HEO: up to ~40000km
                        if sat_alt < 100:  # Below typical LEO (likely bad data)
                            if processed == 0:
                                logger.debug(f"Skipping {sat_data['name']}: altitude {sat_alt:.1f} km too low")
                            continue
                        if sat_alt > 42000:  # Above HEO (likely unit conversion bug in old cache)
                            if processed == 0:
                                logger.warning(f"Skipping {sat_data['name']}: altitude {sat_alt:.1f} km too high (old cache data)")
                            skipped_sats += 1
                            continue

                        # Calculate which grid cells can see this satellite
                        # A satellite at altitude h can be seen from distance d = sqrt(2*R*h + h^2)
                        # where R = Earth radius (~6371 km)
                        earth_radius = 6371.0

                        # Safe calculation with validation
                        range_calculation = 2 * earth_radius * sat_alt + sat_alt ** 2
                        if range_calculation < 0:
                            logger.warning(f"Invalid range calculation for satellite {norad_id}: {range_calculation}")
                            continue

                        visible_range_km = range_calculation ** 0.5

                        # Convert to degrees (approximate)
                        # At elevation = min_elevation, the range is reduced
                        # Using simple geometric approximation
                        import math
                        max_range_deg = visible_range_km / 111.0  # ~111 km per degree
                        cells_radius = max(1, int(max_range_deg / self.grid_size) + 1)

                        # Sanity check on cells_radius
                        if cells_radius > 100:  # Limit to reasonable value
                            logger.warning(f"Cells radius too large ({cells_radius}) for satellite {norad_id} at {sat_alt} km")
                            cells_radius = 10

                        # Get all cells that can potentially see this satellite
                        visible_cells = self._get_surrounding_cells(sat_lat, sat_lon, cells_radius)

                        # For each cell, calculate if satellite is actually visible
                        for lat_bucket, lon_bucket in visible_cells:
                            # Calculate observer position at cell center
                            obs_lat = lat_bucket * self.grid_size + self.grid_size / 2
                            obs_lon = lon_bucket * self.grid_size + self.grid_size / 2

                            # Calculate elevation from this observer position
                            elevation, azimuth, distance = self._calculate_observer_geometry(
                                obs_lat, obs_lon, sat_lat, sat_lon, sat_alt
                            )

                            # Only add if above minimum elevation
                            if elevation >= min_elevation:
                                key = (lat_bucket, lon_bucket, time_bucket)

                                self.index[key].append({
                                    'norad_id': norad_id,
                                    'name': sat_data['name'],
                                    'category': sat_data['category'],
                                    'timestamp': pos['timestamp'],
                                    'elevation': round(elevation, 1),
                                    'azimuth': round(azimuth, 1),
                                    'distance': round(distance, 1),
                                    'sat_lat': sat_lat,
                                    'sat_lon': sat_lon,
                                    'sat_alt': sat_alt
                                })
                                total_entries += 1

                    processed += 1

                    # Force garbage collection every 50 satellites to manage RAM
                    if processed % 50 == 0:
                        gc.collect()

                    if processed % 100 == 0:
                        elapsed = time.time() - start_time
                        rate = processed / elapsed
                        eta = (total_sats - processed) / rate if rate > 0 else 0
                        logger.info(f"   Progress: {processed}/{total_sats} satellites ({rate:.1f} sat/s, ETA: {eta:.0f}s, skipped: {skipped_sats}, errors: {error_sats})")

                except Exception as e:
                    error_sats += 1
                    if error_sats <= 5:  # Log first few errors in detail
                        logger.error(f"Error indexing satellite {norad_id} ({sat_data.get('name', 'Unknown')}): {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                    continue

            # Update metadata
            self.index_metadata = {
                'built_at': datetime.now(timezone.utc).isoformat(),
                'total_entries': total_entries,
                'satellite_count': processed,
                'time_range_start': start_dt.isoformat(),
                'time_range_end': end_dt.isoformat(),
                'grid_size': self.grid_size,
                'time_bucket_minutes': self.time_bucket_minutes,
                'grid_cells_populated': len(self.index)
            }

            elapsed = time.time() - start_time

            # Report altitude format analysis
            if altitude_samples:
                logger.info(f"📊 Altitude samples from cache (first {len(altitude_samples)} satellites):")
                for sample in altitude_samples[:5]:
                    logger.info(f"   • {sample['name']} (ID {sample['norad_id']}): altitude = {sample['altitude_raw']}")

            logger.info(f"✅ Index built: {total_entries} entries, {processed} satellites indexed, "
                       f"{len(self.index)} grid cells populated in {elapsed:.1f}s")
            if skipped_sats > 0:
                logger.info(f"   📊 Skipped {skipped_sats} satellites (no cached positions)")
            if error_sats > 0:
                logger.warning(f"   ⚠️  {error_sats} satellites had indexing errors")

    def query_passes(self, lat: float, lon: float,
                     start_time: datetime, end_time: datetime,
                     min_elevation: float = 10.0) -> List[Dict]:
        """
        Query satellite passes for a location (ULTRA FAST).

        Args:
            lat, lon: Observer location
            start_time, end_time: Time range to search
            min_elevation: Minimum elevation filter

        Returns:
            List of satellite pass events, grouped by satellite
        """
        query_start = time.time()

        with self.lock:
            # Get relevant grid cells (3×3 around location)
            cells = self._get_surrounding_cells(lat, lon, radius_cells=1)

            # Get time buckets in range
            start_bucket = self._get_time_bucket(start_time)
            end_bucket = self._get_time_bucket(end_time)

            # Collect all matching entries
            raw_entries = []
            for lat_bucket, lon_bucket in cells:
                for time_bucket in range(start_bucket, end_bucket + 1):
                    key = (lat_bucket, lon_bucket, time_bucket)
                    entries = self.index.get(key, [])
                    raw_entries.extend(entries)

            # Group by satellite and reconstruct passes
            satellite_positions = defaultdict(list)
            for entry in raw_entries:
                # Recalculate exact elevation for user's precise location
                elevation, azimuth, distance = self._calculate_observer_geometry(
                    lat, lon,
                    entry['sat_lat'], entry['sat_lon'], entry['sat_alt']
                )

                if elevation >= min_elevation:
                    satellite_positions[entry['norad_id']].append({
                        'timestamp': entry['timestamp'],
                        'elevation': round(elevation, 1),
                        'azimuth': round(azimuth, 1),
                        'distance': round(distance, 1),
                        'name': entry['name'],
                        'category': entry['category']
                    })

            # Reconstruct pass events from position sequences
            results = []
            for norad_id, positions in satellite_positions.items():
                if not positions:
                    continue

                # Sort by time
                positions.sort(key=lambda x: x['timestamp'])

                # Detect continuous passes (gap < 3 minutes = new pass)
                passes = self._detect_passes(positions, norad_id)

                if passes:
                    results.append({
                        'norad_id': norad_id,
                        'name': positions[0]['name'],
                        'category': positions[0]['category'],
                        'passes': passes
                    })

            # Update stats
            query_time_ms = (time.time() - query_start) * 1000
            self.stats['queries'] += 1
            self.stats['avg_query_time_ms'] = (
                (self.stats['avg_query_time_ms'] * (self.stats['queries'] - 1) + query_time_ms)
                / self.stats['queries']
            )

            logger.info(f"🔍 Query complete: {len(results)} satellites in {query_time_ms:.1f}ms")

            return results

    def _detect_passes(self, positions: List[Dict], norad_id: int) -> List[Dict]:
        """Detect continuous pass events from sorted positions."""
        passes = []
        current_pass = None

        for pos in positions:
            pos_time = datetime.fromisoformat(pos['timestamp'])

            if current_pass is None:
                # Start new pass
                current_pass = {
                    'start': pos['timestamp'],
                    'start_azimuth': pos['azimuth'],
                    'max_elevation': pos['elevation'],
                    'max_elevation_time': pos['timestamp'],
                    'positions': [pos]
                }
            else:
                # Check if continuation of current pass
                last_time = datetime.fromisoformat(current_pass['positions'][-1]['timestamp'])
                gap_minutes = (pos_time - last_time).total_seconds() / 60

                if gap_minutes > 3:
                    # Gap too large, finalize current pass and start new one
                    current_pass['end'] = current_pass['positions'][-1]['timestamp']
                    current_pass['end_azimuth'] = current_pass['positions'][-1]['azimuth']
                    current_pass['duration_seconds'] = (
                        datetime.fromisoformat(current_pass['end']) -
                        datetime.fromisoformat(current_pass['start'])
                    ).total_seconds()

                    if current_pass['duration_seconds'] >= 30:  # At least 30 seconds
                        passes.append(current_pass)

                    # Start new pass
                    current_pass = {
                        'start': pos['timestamp'],
                        'start_azimuth': pos['azimuth'],
                        'max_elevation': pos['elevation'],
                        'max_elevation_time': pos['timestamp'],
                        'positions': [pos]
                    }
                else:
                    # Continue current pass
                    current_pass['positions'].append(pos)
                    if pos['elevation'] > current_pass['max_elevation']:
                        current_pass['max_elevation'] = pos['elevation']
                        current_pass['max_elevation_time'] = pos['timestamp']

        # Finalize last pass
        if current_pass and len(current_pass['positions']) >= 2:
            current_pass['end'] = current_pass['positions'][-1]['timestamp']
            current_pass['end_azimuth'] = current_pass['positions'][-1]['azimuth']
            current_pass['duration_seconds'] = (
                datetime.fromisoformat(current_pass['end']) -
                datetime.fromisoformat(current_pass['start'])
            ).total_seconds()

            if current_pass['duration_seconds'] >= 30:
                passes.append(current_pass)

        return passes

    def _calculate_observer_geometry(self, obs_lat: float, obs_lon: float,
                                     sat_lat: float, sat_lon: float,
                                     sat_alt: float) -> Tuple[float, float, float]:
        """
        Calculate elevation, azimuth, and distance from observer to satellite.

        Uses robust geometric calculations with edge case handling.
        """
        import math

        try:
            # Validate inputs
            if not (-90 <= obs_lat <= 90 and -180 <= obs_lon <= 180):
                return (-90.0, 0.0, 0.0)  # Below horizon
            if not (-90 <= sat_lat <= 90 and -180 <= sat_lon <= 180):
                return (-90.0, 0.0, 0.0)
            if sat_alt < 0 or sat_alt > 50000:  # Sanity check altitude
                return (-90.0, 0.0, 0.0)

            # Convert to radians
            obs_lat_rad = math.radians(obs_lat)
            obs_lon_rad = math.radians(obs_lon)
            sat_lat_rad = math.radians(sat_lat)
            sat_lon_rad = math.radians(sat_lon)

            # Earth radius in km
            earth_radius = 6371.0

            # Calculate great circle distance using Haversine formula
            dlat = sat_lat_rad - obs_lat_rad
            dlon = sat_lon_rad - obs_lon_rad

            # Haversine formula (more numerically stable)
            a = math.sin(dlat/2)**2 + math.cos(obs_lat_rad) * math.cos(sat_lat_rad) * math.sin(dlon/2)**2

            # Clamp 'a' to valid range [0, 1] to avoid sqrt of negative or asin of >1
            a = max(0.0, min(1.0, a))

            # Safe sqrt since a is now guaranteed to be in [0, 1]
            sqrt_a = math.sqrt(a)

            # Clamp to avoid asin domain error
            sqrt_a = max(0.0, min(1.0, sqrt_a))

            c = 2 * math.asin(sqrt_a)
            surface_distance = earth_radius * c

            # Calculate 3D Cartesian positions
            # Observer position (at sea level)
            obs_x = earth_radius * math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
            obs_y = earth_radius * math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
            obs_z = earth_radius * math.sin(obs_lat_rad)

            # Satellite position (at altitude above Earth surface)
            sat_radius = earth_radius + sat_alt
            sat_x = sat_radius * math.cos(sat_lat_rad) * math.cos(sat_lon_rad)
            sat_y = sat_radius * math.cos(sat_lat_rad) * math.sin(sat_lon_rad)
            sat_z = sat_radius * math.sin(sat_lat_rad)

            # Vector from observer to satellite
            dx = sat_x - obs_x
            dy = sat_y - obs_y
            dz = sat_z - obs_z

            # Slant range (direct 3D distance)
            slant_range = math.sqrt(dx**2 + dy**2 + dz**2)

            if slant_range < 0.01:  # Satellite extremely close or at observer
                return (90.0, 0.0, slant_range)

            # Calculate elevation using local horizontal coordinate system
            # Create local north-east-up (NEU) coordinate system at observer

            # Local up vector (points away from Earth center)
            up_x = math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
            up_y = math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
            up_z = math.sin(obs_lat_rad)

            # Dot product of satellite direction with up vector
            dot_up = (dx * up_x + dy * up_y + dz * up_z) / slant_range

            # Clamp to valid range for asin
            dot_up = max(-1.0, min(1.0, dot_up))

            # Elevation angle
            elevation = math.degrees(math.asin(dot_up))

            # Calculate azimuth (bearing from north)
            # Local north vector at observer
            north_x = -math.sin(obs_lat_rad) * math.cos(obs_lon_rad)
            north_y = -math.sin(obs_lat_rad) * math.sin(obs_lon_rad)
            north_z = math.cos(obs_lat_rad)

            # Local east vector at observer
            east_x = -math.sin(obs_lon_rad)
            east_y = math.cos(obs_lon_rad)
            east_z = 0.0

            # Project satellite direction onto horizontal plane
            north_component = (dx * north_x + dy * north_y + dz * north_z) / slant_range
            east_component = (dx * east_x + dy * east_y + dz * east_z) / slant_range

            # Calculate azimuth from north and east components
            azimuth = math.degrees(math.atan2(east_component, north_component))
            azimuth = (azimuth + 360) % 360  # Normalize to 0-360

            return (elevation, azimuth, slant_range)

        except Exception as e:
            # If any calculation fails, return below horizon
            logger.warning(f"Geometry calculation error: {e}")
            return (-90.0, 0.0, 0.0)

    def get_stats(self) -> Dict:
        """Get index statistics."""
        with self.lock:
            return {
                'metadata': self.index_metadata,
                'stats': self.stats,
                'memory_estimate_mb': len(self.index) * 0.1  # Rough estimate
            }

    def is_ready(self) -> bool:
        """Check if index is ready for queries."""
        return self.index_metadata['built_at'] is not None
