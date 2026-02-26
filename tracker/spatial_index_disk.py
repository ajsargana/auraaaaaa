"""
Disk-Based Spatial-Temporal Index for Ultra-Fast Satellite Pass Queries

This version uses SQLite for disk-based storage to avoid RAM issues.
Processes satellites in batches and saves incrementally.

Features:
- Low RAM usage (~500MB max instead of 15GB+)
- Resumable builds (can stop and continue)
- Fast queries using indexed SQLite database
"""

import gc
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import math

logger = logging.getLogger(__name__)


class DiskSpatialIndex:
    """
    Disk-based spatial-temporal index for satellite pass predictions.

    Uses SQLite database to store index on disk, avoiding RAM issues.
    """

    def __init__(self, db_path: str = "cache/spatial_index.db",
                 grid_size: float = 5.0, time_bucket_minutes: int = 1):
        """
        Initialize the disk-based spatial-temporal index.

        Args:
            db_path: Path to SQLite database file
            grid_size: Grid cell size in degrees (default 5°)
            time_bucket_minutes: Time bucket size in minutes (default 1 min)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.grid_size = grid_size
        self.time_bucket_minutes = time_bucket_minutes

        # Initialize database
        self._init_database()

        logger.info(f"🗺️ Disk-based Spatial Index initialized at {db_path}")

    def _init_database(self):
        """Initialize SQLite database with optimized schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create main index table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spatial_index (
                lat_bucket INTEGER,
                lon_bucket INTEGER,
                time_bucket INTEGER,
                norad_id INTEGER,
                name TEXT,
                category TEXT,
                timestamp TEXT,
                elevation REAL,
                azimuth REAL,
                distance REAL,
                sat_lat REAL,
                sat_lon REAL,
                sat_alt REAL,
                PRIMARY KEY (lat_bucket, lon_bucket, time_bucket, norad_id, timestamp)
            )
        """)

        # Create indexes for fast queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_location_time
            ON spatial_index(lat_bucket, lon_bucket, time_bucket)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_norad
            ON spatial_index(norad_id)
        """)

        # Create metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Create progress tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS build_progress (
                norad_id INTEGER PRIMARY KEY,
                completed INTEGER,
                timestamp TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _get_grid_cell(self, lat: float, lon: float) -> Tuple[int, int]:
        """Convert lat/lon to grid cell coordinates."""
        lat_bucket = int(lat / self.grid_size)
        lon_bucket = int(lon / self.grid_size)
        return (lat_bucket, lon_bucket)

    def _get_time_bucket(self, timestamp: datetime) -> int:
        """Convert timestamp to time bucket (minutes since epoch)."""
        return int(timestamp.timestamp() / (self.time_bucket_minutes * 60))

    def _get_surrounding_cells(self, lat: float, lon: float,
                               radius_cells: int = 1) -> List[Tuple[int, int]]:
        """Get surrounding grid cells for a location."""
        center_lat, center_lon = self._get_grid_cell(lat, lon)
        cells = []

        for lat_offset in range(-radius_cells, radius_cells + 1):
            for lon_offset in range(-radius_cells, radius_cells + 1):
                lat_bucket = center_lat + lat_offset
                lon_bucket = center_lon + lon_offset

                # Clamp latitude buckets
                if lat_bucket < -18 or lat_bucket > 18:
                    continue

                # Wrap longitude buckets
                lon_bucket = lon_bucket % int(360 / self.grid_size)

                cells.append((lat_bucket, lon_bucket))

        return cells

    def build_index_incremental(self, position_cache_manager,
                                time_window_hours: int = 48,
                                min_elevation: float = 10.0,
                                batch_size: int = 10) -> None:
        """
        Build the spatial-temporal index incrementally with progress saving.

        Processes satellites in small batches and saves to disk immediately.
        Can be stopped and resumed.

        Args:
            position_cache_manager: The OptimizedPositionCacheManager instance
            time_window_hours: How many hours ahead to index (default 48 = 2 days)
            min_elevation: Minimum elevation to consider (degrees)
            batch_size: Number of satellites to process before saving (default 10)
        """
        logger.info(f"🏗️ Building disk-based spatial index ({time_window_hours}h window)...")
        logger.info(f"   Batch size: {batch_size} satellites")
        logger.info(f"   RAM-efficient: saves to disk after each batch")

        start_time = datetime.now(timezone.utc)
        start_dt = start_time
        end_dt = start_time + timedelta(hours=time_window_hours)

        satellites = position_cache_manager.satellite_manager.satellites
        total_sats = len(satellites)

        # Get list of completed satellites
        completed_sats = self._get_completed_satellites()
        remaining_sats = [nid for nid in satellites.keys() if nid not in completed_sats]

        if completed_sats:
            logger.info(f"   📊 Resuming: {len(completed_sats)} already done, {len(remaining_sats)} remaining")

        processed = len(completed_sats)
        total_entries = 0
        skipped_sats = 0
        error_sats = 0

        # Process in batches
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        batch = []
        for norad_id in remaining_sats:
            sat_data = satellites[norad_id]

            try:
                # Get cached positions for this satellite
                positions = position_cache_manager.get_position_range(
                    norad_id, start_dt, end_dt, interval_seconds=60
                )

                if not positions or len(positions) < 2:
                    skipped_sats += 1
                    continue

                # Process each position
                entries_for_sat = []
                for pos in positions:
                    pos_time = datetime.fromisoformat(pos['timestamp'])
                    time_bucket = self._get_time_bucket(pos_time)

                    sat_lat = pos['latitude']
                    sat_lon = pos['longitude']
                    sat_alt = pos['altitude']

                    # Validate coordinates
                    if not (-90 <= sat_lat <= 90 and -180 <= sat_lon <= 180):
                        continue

                    # Validate altitude range (LEO to GEO: 100 km to 42,000 km)
                    if sat_alt < 100 or sat_alt > 42000:
                        continue

                    # OPTIMIZED: Only store satellite in its own grid cell
                    # Query time will check surrounding cells
                    lat_bucket, lon_bucket = self._get_grid_cell(sat_lat, sat_lon)

                    entries_for_sat.append((
                        lat_bucket, lon_bucket, time_bucket,
                        norad_id, sat_data['name'], sat_data['category'],
                        pos['timestamp'],
                        0.0, 0.0, 0.0,  # Elevation/azimuth/distance calculated at query time
                        sat_lat, sat_lon, sat_alt
                    ))

                if entries_for_sat:
                    # Insert all entries for this satellite
                    cursor.executemany("""
                        INSERT OR REPLACE INTO spatial_index VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, entries_for_sat)
                    total_entries += len(entries_for_sat)

                # Mark satellite as completed
                cursor.execute("""
                    INSERT OR REPLACE INTO build_progress VALUES (?, 1, ?)
                """, (norad_id, datetime.now(timezone.utc).isoformat()))

                processed += 1
                batch.append(norad_id)

                # Commit every batch_size satellites
                if len(batch) >= batch_size:
                    conn.commit()
                    gc.collect()  # Free memory

                    # Get database size
                    cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
                    db_size = cursor.fetchone()[0] / (1024 * 1024)  # MB

                    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                    rate = processed / elapsed if elapsed > 0 else 0
                    eta = (total_sats - processed) / rate if rate > 0 else 0
                    entries_per_sat = total_entries / processed if processed > 0 else 0

                    logger.info(f"   ✓ Batch saved: {processed}/{total_sats} satellites "
                               f"({rate:.1f} sat/s, ETA: {eta/60:.0f}min) | "
                               f"{total_entries:,} entries ({entries_per_sat:.0f}/sat) | "
                               f"DB: {db_size:.1f}MB")
                    batch = []

            except Exception as e:
                error_sats += 1
                if error_sats <= 5:
                    logger.error(f"Error indexing satellite {norad_id}: {e}")
                continue

        # Final commit
        if batch:
            conn.commit()

        # Update metadata
        metadata = {
            'built_at': datetime.now(timezone.utc).isoformat(),
            'total_entries': total_entries,
            'satellite_count': processed,
            'time_range_start': start_dt.isoformat(),
            'time_range_end': end_dt.isoformat(),
            'grid_size': self.grid_size,
            'time_bucket_minutes': self.time_bucket_minutes
        }

        for key, value in metadata.items():
            cursor.execute("""
                INSERT OR REPLACE INTO metadata VALUES (?, ?)
            """, (key, json.dumps(value)))

        conn.commit()
        conn.close()

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(f"✅ Index built: {total_entries:,} entries, {processed} satellites in {elapsed:.1f}s")
        if skipped_sats > 0:
            logger.info(f"   📊 Skipped {skipped_sats} satellites (no cached positions)")

    def _get_completed_satellites(self) -> set:
        """Get set of satellite IDs that have been fully processed"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT norad_id FROM build_progress WHERE completed = 1")
        completed = {row[0] for row in cursor.fetchall()}
        conn.close()
        return completed

    def query_passes(self, lat: float, lon: float,
                     start_time: datetime, end_time: datetime,
                     min_elevation: float = 10.0) -> List[Dict]:
        """
        Query satellite passes for a location (disk-based, low RAM).

        Args:
            lat, lon: Observer location
            start_time, end_time: Time range to search
            min_elevation: Minimum elevation filter

        Returns:
            List of satellite pass events, grouped by satellite
        """
        from collections import defaultdict
        import time as time_module

        query_start = time_module.time()

        # Get relevant grid cells - check wider radius to catch all visible satellites
        # At 10° elevation, max distance is ~1000km = ~9° = ~2 grid cells @ 5° grid
        cells = self._get_surrounding_cells(lat, lon, radius_cells=3)

        # Get time buckets
        start_bucket = self._get_time_bucket(start_time)
        end_bucket = self._get_time_bucket(end_time)

        # Query database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Build query for all cells and time buckets
        placeholders = ','.join(['(?,?)'] * len(cells))
        query = f"""
            SELECT * FROM spatial_index
            WHERE (lat_bucket, lon_bucket) IN ({placeholders})
            AND time_bucket BETWEEN ? AND ?
        """

        params = []
        for lat_bucket, lon_bucket in cells:
            params.extend([lat_bucket, lon_bucket])
        params.extend([start_bucket, end_bucket])

        cursor.execute(query, params)

        # Process results
        satellite_positions = defaultdict(list)
        for row in cursor:
            sat_lat, sat_lon, sat_alt = row[10], row[11], row[12]

            # Recalculate exact elevation for user's precise location
            elevation, azimuth, distance = self._calculate_observer_geometry(
                lat, lon, sat_lat, sat_lon, sat_alt
            )

            if elevation >= min_elevation:
                satellite_positions[row[3]].append({  # norad_id
                    'timestamp': row[6],
                    'elevation': round(elevation, 1),
                    'azimuth': round(azimuth, 1),
                    'distance': round(distance, 1),
                    'name': row[4],
                    'category': row[5]
                })

        conn.close()

        # Reconstruct pass events
        results = []
        for norad_id, positions in satellite_positions.items():
            if not positions:
                continue

            positions.sort(key=lambda x: x['timestamp'])
            passes = self._detect_passes(positions, norad_id)

            if passes:
                results.append({
                    'norad_id': norad_id,
                    'name': positions[0]['name'],
                    'category': positions[0]['category'],
                    'passes': passes
                })

        query_time_ms = (time_module.time() - query_start) * 1000
        logger.info(f"🔍 Query complete: {len(results)} satellites in {query_time_ms:.1f}ms")

        return results

    def _detect_passes(self, positions: List[Dict], norad_id: int) -> List[Dict]:
        """Detect continuous pass events from sorted positions."""
        passes = []
        current_pass = None

        for pos in positions:
            pos_time = datetime.fromisoformat(pos['timestamp'])

            if current_pass is None:
                current_pass = {
                    'start': pos['timestamp'],
                    'start_azimuth': pos['azimuth'],
                    'max_elevation': pos['elevation'],
                    'max_elevation_time': pos['timestamp'],
                    'positions': [pos]
                }
            else:
                last_time = datetime.fromisoformat(current_pass['positions'][-1]['timestamp'])
                gap_minutes = (pos_time - last_time).total_seconds() / 60

                if gap_minutes > 3:
                    # Finalize current pass
                    current_pass['end'] = current_pass['positions'][-1]['timestamp']
                    current_pass['end_azimuth'] = current_pass['positions'][-1]['azimuth']
                    current_pass['duration_seconds'] = (
                        datetime.fromisoformat(current_pass['end']) -
                        datetime.fromisoformat(current_pass['start'])
                    ).total_seconds()

                    if current_pass['duration_seconds'] >= 30:
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
        """Calculate elevation, azimuth, and distance from observer to satellite."""
        try:
            if not (-90 <= obs_lat <= 90 and -180 <= obs_lon <= 180):
                return (-90.0, 0.0, 0.0)
            if not (-90 <= sat_lat <= 90 and -180 <= sat_lon <= 180):
                return (-90.0, 0.0, 0.0)
            if sat_alt < 0 or sat_alt > 50000:
                return (-90.0, 0.0, 0.0)

            obs_lat_rad = math.radians(obs_lat)
            obs_lon_rad = math.radians(obs_lon)
            sat_lat_rad = math.radians(sat_lat)
            sat_lon_rad = math.radians(sat_lon)

            earth_radius = 6371.0

            # Haversine distance
            dlat = sat_lat_rad - obs_lat_rad
            dlon = sat_lon_rad - obs_lon_rad
            a = math.sin(dlat/2)**2 + math.cos(obs_lat_rad) * math.cos(sat_lat_rad) * math.sin(dlon/2)**2
            a = max(0.0, min(1.0, a))
            c = 2 * math.asin(math.sqrt(a))
            surface_distance = earth_radius * c

            # 3D positions
            obs_x = earth_radius * math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
            obs_y = earth_radius * math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
            obs_z = earth_radius * math.sin(obs_lat_rad)

            sat_radius = earth_radius + sat_alt
            sat_x = sat_radius * math.cos(sat_lat_rad) * math.cos(sat_lon_rad)
            sat_y = sat_radius * math.cos(sat_lat_rad) * math.sin(sat_lon_rad)
            sat_z = sat_radius * math.sin(sat_lat_rad)

            dx = sat_x - obs_x
            dy = sat_y - obs_y
            dz = sat_z - obs_z

            slant_range = math.sqrt(dx**2 + dy**2 + dz**2)
            if slant_range < 0.01:
                return (90.0, 0.0, slant_range)

            # Local up vector
            up_x = math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
            up_y = math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
            up_z = math.sin(obs_lat_rad)

            dot_up = (dx * up_x + dy * up_y + dz * up_z) / slant_range
            dot_up = max(-1.0, min(1.0, dot_up))
            elevation = math.degrees(math.asin(dot_up))

            # Azimuth
            north_x = -math.sin(obs_lat_rad) * math.cos(obs_lon_rad)
            north_y = -math.sin(obs_lat_rad) * math.sin(obs_lon_rad)
            north_z = math.cos(obs_lat_rad)

            east_x = -math.sin(obs_lon_rad)
            east_y = math.cos(obs_lon_rad)
            east_z = 0.0

            north_component = (dx * north_x + dy * north_y + dz * north_z) / slant_range
            east_component = (dx * east_x + dy * east_y + dz * east_z) / slant_range

            azimuth = math.degrees(math.atan2(east_component, north_component))
            azimuth = (azimuth + 360) % 360

            return (elevation, azimuth, slant_range)

        except Exception as e:
            logger.warning(f"Geometry calculation error: {e}")
            return (-90.0, 0.0, 0.0)

    def is_ready(self) -> bool:
        """Check if index is ready for queries."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM metadata WHERE key = 'built_at'")
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except:
            return False

    def get_stats(self) -> Dict:
        """Get index statistics."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get metadata
            cursor.execute("SELECT key, value FROM metadata")
            metadata = {row[0]: json.loads(row[1]) for row in cursor.fetchall()}

            # Get entry count
            cursor.execute("SELECT COUNT(*) FROM spatial_index")
            entry_count = cursor.fetchone()[0]

            # Get database size
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size_bytes = cursor.fetchone()[0]

            conn.close()

            return {
                'metadata': metadata,
                'entry_count': entry_count,
                'db_size_mb': db_size_bytes / (1024 * 1024),
                'stats': {'queries': 0, 'avg_query_time_ms': 0}
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'metadata': {}, 'entry_count': 0, 'db_size_mb': 0}

    def clear_progress(self):
        """Clear build progress (for fresh rebuild)"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM build_progress")
        cursor.execute("DELETE FROM spatial_index")
        cursor.execute("DELETE FROM metadata")
        conn.commit()
        conn.close()
        logger.info("✓ Cleared index and progress")
