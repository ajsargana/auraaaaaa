#!/usr/bin/env python3

import gc
import os
import json
import logging
import threading
import time
import tempfile
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import OrderedDict, defaultdict
from skyfield.api import wgs84, Topos
import hashlib
import concurrent.futures
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU cache for frequently accessed satellite data"""
    def __init__(self, max_size=100):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]
            self.misses += 1
        return None

    def put(self, key, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.max_size:
                    self.cache.popitem(last=False)
            self.cache[key] = value

    def clear(self):
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self):
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': f"{hit_rate:.1f}%",
                'size': len(self.cache)
            }


class ChunkedDataStore:
    """Efficient chunked storage for large satellite datasets"""

    def __init__(self, cache_dir: Path, chunk_duration_hours: float = 1.0):
        self.cache_dir = cache_dir
        self.chunk_duration = timedelta(hours=chunk_duration_hours)
        self.chunk_cache = LRUCache(max_size=50)  # In-memory cache for chunks

    def _get_chunk_id(self, norad_id: int, timestamp: datetime, stage: str) -> str:
        """Generate chunk ID for given timestamp"""
        chunk_start = timestamp.replace(minute=0, second=0, microsecond=0)
        return f"{stage}_{norad_id}_{chunk_start.strftime('%Y%m%d_%H')}"

    def save_chunked_data(self, norad_id: int, data: Dict, stage_name: str):
        """Save data in hourly chunks with comprehensive metadata for production-grade caching"""
        chunks = defaultdict(lambda: {
            # Position and velocity vectors (ECI frame - CANONICAL for orbit visualization)
            'epochs': [], 'timestamps': [], 'latitudes': [], 
            'longitudes': [], 'altitudes': [],
            # ECI state vector (canonical inertial frame for orbit rendering)
            'eci_x': [], 'eci_y': [], 'eci_z': [],
            'eci_vx': [], 'eci_vy': [], 'eci_vz': [],
            # ECEF frame (for ground station geometry only)
            'ecef_x': [], 'ecef_y': [], 'ecef_z': [],
            'ecef_vx': [], 'ecef_vy': [], 'ecef_vz': []
        })

        # Group data by hour chunks
        for i in range(len(data['epochs'])):
            ts = datetime.fromtimestamp(data['epochs'][i], tz=timezone.utc)
            chunk_id = self._get_chunk_id(norad_id, ts, stage_name)

            for key in chunks[chunk_id].keys():
                if key in data and i < len(data[key]):
                    chunks[chunk_id][key].append(data[key][i])

        # Save each chunk with comprehensive metadata
        for chunk_id, chunk_data in chunks.items():
            chunk_file = self.cache_dir / f"{chunk_id}.npz"

            with tempfile.NamedTemporaryFile(
                mode='wb', dir=self.cache_dir, delete=False,
                prefix=f'tmp_{chunk_id}_', suffix='.npz'
            ) as tmp_file:
                np.savez_compressed(
                    tmp_file,
                    # Position/velocity data
                    epochs=np.array(chunk_data['epochs'], dtype=np.float64),
                    timestamps=np.array(chunk_data['timestamps'], dtype='U26'),
                    latitudes=np.array(chunk_data['latitudes'], dtype=np.float32),
                    longitudes=np.array(chunk_data['longitudes'], dtype=np.float32),
                    altitudes=np.array(chunk_data['altitudes'], dtype=np.float32),
                    # ECI state vector (canonical inertial frame for orbit rendering)
                    eci_x=np.array(chunk_data['eci_x'], dtype=np.float64),
                    eci_y=np.array(chunk_data['eci_y'], dtype=np.float64),
                    eci_z=np.array(chunk_data['eci_z'], dtype=np.float64),
                    eci_vx=np.array(chunk_data['eci_vx'], dtype=np.float64),
                    eci_vy=np.array(chunk_data['eci_vy'], dtype=np.float64),
                    eci_vz=np.array(chunk_data['eci_vz'], dtype=np.float64),
                    # ECEF frame (for ground station geometry only)
                    ecef_x=np.array(chunk_data['ecef_x'], dtype=np.float64),
                    ecef_y=np.array(chunk_data['ecef_y'], dtype=np.float64),
                    ecef_z=np.array(chunk_data['ecef_z'], dtype=np.float64),
                    ecef_vx=np.array(chunk_data['ecef_vx'], dtype=np.float64),
                    ecef_vy=np.array(chunk_data['ecef_vy'], dtype=np.float64),
                    ecef_vz=np.array(chunk_data['ecef_vz'], dtype=np.float64),
                    # Metadata
                    name=np.array([data.get('name', 'Unknown')], dtype='U100'),
                    reference_frame=np.array(['ECI'], dtype='U10'),  # ECI for orbit visualization
                    timescale=np.array(['UTC'], dtype='U10'),  # UTC timescale
                    earth_model=np.array(['WGS84'], dtype='U10'),  # WGS84 ellipsoid
                    tle_hash=np.array([data.get('tle_hash', '')], dtype='U64'),  # TLE tracking
                    tle_epoch=np.array([data.get('tle_epoch', 0.0)], dtype=np.float64),
                    # Orbital elements (derived from TLE)
                    semi_major_axis=np.array([data.get('semi_major_axis', 0.0)], dtype=np.float64),
                    eccentricity=np.array([data.get('eccentricity', 0.0)], dtype=np.float64),
                    inclination=np.array([data.get('inclination', 0.0)], dtype=np.float64),
                    raan=np.array([data.get('raan', 0.0)], dtype=np.float64),
                    arg_perigee=np.array([data.get('arg_perigee', 0.0)], dtype=np.float64),
                    mean_anomaly=np.array([data.get('mean_anomaly', 0.0)], dtype=np.float64),
                    orbital_period=np.array([data.get('orbital_period', 0.0)], dtype=np.float64),
                    # Classification
                    orbit_class=np.array([data.get('orbit_class', 'LEO')], dtype='U10'),  # LEO/MEO/GEO/HEO
                    # Cache validity
                    cache_created=np.array([datetime.now(timezone.utc).timestamp()], dtype=np.float64),
                    cache_expiry=np.array([data.get('cache_expiry', 0.0)], dtype=np.float64),
                    # Chunk metadata
                    chunk_start_epoch=np.array([chunk_data['epochs'][0] if chunk_data['epochs'] else 0.0], dtype=np.float64),
                    chunk_end_epoch=np.array([chunk_data['epochs'][-1] if chunk_data['epochs'] else 0.0], dtype=np.float64),
                    is_continuous=np.array([data.get('is_continuous', True)], dtype=bool),
                    time_step_seconds=np.array([15.0], dtype=np.float32)  # Fixed 15s intervals
                )

            os.replace(tmp_file.name, str(chunk_file))

    def load_chunked_data(self, norad_id: int, start_time: datetime, 
                          end_time: datetime, stage: str) -> Optional[Dict]:
        """Load only required chunks for time range with all metadata"""
        combined_data = None
        current_time = start_time.replace(minute=0, second=0, microsecond=0)

        # Metadata fields that should not be filtered/extended
        metadata_fields = {
            'name', 'reference_frame', 'timescale', 'earth_model', 
            'tle_hash', 'tle_epoch', 'semi_major_axis', 'eccentricity',
            'inclination', 'raan', 'arg_perigee', 'mean_anomaly',
            'orbital_period', 'orbit_class', 'cache_created', 'cache_expiry',
            'chunk_start_epoch', 'chunk_end_epoch', 'is_continuous', 'time_step_seconds'
        }

        while current_time <= end_time:
            chunk_id = self._get_chunk_id(norad_id, current_time, stage)

            # Check memory cache first
            chunk_data = self.chunk_cache.get(chunk_id)

            if chunk_data is None:
                chunk_file = self.cache_dir / f"{chunk_id}.npz"
                if chunk_file.exists():
                    try:
                        loaded = np.load(chunk_file, allow_pickle=True)
                        chunk_data = {key: loaded[key] for key in loaded.files}
                        self.chunk_cache.put(chunk_id, chunk_data)
                    except Exception as e:
                        logger.warning(f"Failed to load chunk {chunk_id}: {e}")
                        current_time += timedelta(hours=1)
                        continue

            if chunk_data:
                if combined_data is None:
                    combined_data = {key: [] for key in chunk_data.keys()}

                # Filter data within time range
                epochs = chunk_data.get('epochs')
                if epochs is not None and len(epochs) > 0:
                    start_epoch = start_time.timestamp()
                    end_epoch = end_time.timestamp()
                    mask = (epochs >= start_epoch) & (epochs <= end_epoch)

                    for key in chunk_data.keys():
                        if key in metadata_fields:
                            # Metadata: take first value only
                            if not combined_data[key]:
                                combined_data[key] = chunk_data[key]
                        else:
                            # Time-series data: filter and extend
                            filtered = chunk_data[key][mask] if hasattr(chunk_data[key], '__getitem__') and len(chunk_data[key].shape) > 0 else chunk_data[key]
                            combined_data[key].extend(filtered if hasattr(filtered, '__iter__') and len(filtered.shape) > 0 else [filtered])

            current_time += timedelta(hours=1)

        # Convert lists to numpy arrays (except metadata)
        if combined_data:
            for key in combined_data.keys():
                if key not in metadata_fields and isinstance(combined_data[key], list):
                    dtype = np.float64 if 'ecef' in key or 'eci' in key or 'epoch' in key else np.float32
                    if key == 'timestamps':
                        dtype = 'U26'
                    combined_data[key] = np.array(combined_data[key], dtype=dtype)

        return combined_data


class PassCache:
    """Dedicated cache for satellite pass predictions"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir / 'passes'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pass_cache = {}
        self.lock = threading.Lock()

    def _get_pass_key(self, norad_id: int, lat: float, lon: float, 
                      date: datetime) -> str:
        """Generate unique key for pass cache"""
        date_str = date.strftime('%Y%m%d')
        return f"{norad_id}_{lat:.2f}_{lon:.2f}_{date_str}"

    def save_passes(self, norad_id: int, lat: float, lon: float, 
                   passes: List[Dict], date: datetime):
        """Save calculated passes for a location and date"""
        key = self._get_pass_key(norad_id, lat, lon, date)
        cache_file = self.cache_dir / f"{key}.json"

        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'norad_id': norad_id,
                    'latitude': lat,
                    'longitude': lon,
                    'date': date.isoformat(),
                    'passes': passes,
                    'cached_at': datetime.now(timezone.utc).isoformat()
                }, f, indent=2)

            with self.lock:
                self.pass_cache[key] = passes

        except Exception as e:
            logger.error(f"Error saving pass cache: {e}")

    def get_passes(self, norad_id: int, lat: float, lon: float, 
                  date: datetime) -> Optional[List[Dict]]:
        """Retrieve cached passes if available"""
        key = self._get_pass_key(norad_id, lat, lon, date)

        # Check memory cache
        with self.lock:
            if key in self.pass_cache:
                return self.pass_cache[key]

        # Check disk cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    passes = data['passes']

                    with self.lock:
                        self.pass_cache[key] = passes

                    return passes
            except Exception as e:
                logger.warning(f"Error loading pass cache: {e}")

        return None

    def cleanup_old_passes(self, days_to_keep: int = 7):
        """Remove old pass predictions"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        for cache_file in self.cache_dir.glob('*.json'):
            try:
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    cache_file.unlink()
            except Exception as e:
                logger.warning(f"Error cleaning up pass cache: {e}")


class OptimizedPositionCacheManager:
    def __init__(self, satellite_manager):
        self.satellite_manager = satellite_manager
        self.cache_dir = Path('cache/position_cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Smart incremental cache manager (reduces RAM usage)
        self.smart_cache = None  # Initialized after first use

        self.metadata_file = self.cache_dir / 'cache_metadata.json'

        # FIXED: 15-second intervals for ALL stages
        self.position_interval_seconds = 15

        # Initialize subsystems
        self.chunked_store = ChunkedDataStore(self.cache_dir)
        self.pass_cache = PassCache(self.cache_dir)
        self.memory_cache = LRUCache(max_size=100)

        # Thread pool for parallel processing
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

        self.priority_satellites = []
        self.on_demand_cache = {}

        self.cache_stages = {
            'stage1': {
                'duration_minutes': 5,
                'status': 'pending',
                'satellite_count': 0,
                'interval_seconds': 15  # Consistent 15s
            },
            'stage2': {
                'duration_hours': 4,
                'status': 'pending',
                'satellite_count': 0,
                'interval_seconds': 15  # Consistent 15s
            },
            'stage3': {
                'duration': 'rest_of_day',
                'status': 'pending',
                'satellite_count': 0,
                'interval_seconds': 15  # Consistent 15s
            },
            'stage4': {
                'duration_days': 2,
                'status': 'pending',
                'satellite_count': 0,
                'interval_seconds': 15  # Consistent 15s
            },
        }

        self.background_threads = []
        self.cache_lock = threading.Lock()

        # Performance metrics
        self.metrics = {
            'calculations_performed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'interpolations_performed': 0,
            'passes_calculated': 0
        }

        self._load_metadata()
        self._identify_priority_satellites()

    def _extract_orbital_elements(self, satellite) -> Dict:
        """Extract orbital elements from satellite TLE"""
        try:
            import math

            # Handle both Satrec objects and EarthSatellite objects
            if hasattr(satellite, 'model'):
                model = satellite.model
            else:
                model = satellite

            # Inclination (radians to degrees)
            inclination = math.degrees(model.inclo)

            # Eccentricity
            eccentricity = model.ecco

            # Mean motion (radians/minute to revolutions/day)
            mean_motion_rad_min = model.no_kozai
            n = mean_motion_rad_min * (24 * 60) / (2 * math.pi)

            # Semi-major axis from mean motion (Kepler's third law)
            mu = 398600.4418  # Earth's gravitational parameter (km^3/s^2)
            period_seconds = (24 * 3600) / n
            semi_major_axis = ((mu * (period_seconds / (2 * math.pi))**2)**(1/3))

            # RAAN (Right Ascension of Ascending Node)
            raan = math.degrees(model.nodeo)

            # Argument of perigee
            arg_perigee = math.degrees(model.argpo)

            # Mean anomaly
            mean_anomaly = math.degrees(model.mo)

            # Orbital period (minutes)
            orbital_period = period_seconds / 60

            return {
                'semi_major_axis': semi_major_axis,
                'eccentricity': eccentricity,
                'inclination': inclination,
                'raan': raan,
                'arg_perigee': arg_perigee,
                'mean_anomaly': mean_anomaly,
                'orbital_period': orbital_period
            }
        except Exception as e:
            logger.warning(f"Error extracting orbital elements: {e}")
            return {
                'semi_major_axis': 6771.0,
                'eccentricity': 0.0,
                'inclination': 0.0,
                'raan': 0.0,
                'arg_perigee': 0.0,
                'mean_anomaly': 0.0,
                'orbital_period': 90.0
            }

    def _classify_orbit(self, semi_major_axis: float) -> str:
        """Classify orbit type based on semi-major axis"""
        altitude = semi_major_axis - 6371.0  # Convert to altitude above Earth

        if altitude < 2000:
            return 'LEO'  # Low Earth Orbit
        elif 35586 <= altitude <= 35986:
            return 'GEO'  # Geostationary Orbit (±200km tolerance)
        elif 2000 <= altitude < 35586:
            return 'MEO'  # Medium Earth Orbit
        else:
            return 'HEO'  # High Earth Orbit

    def _load_metadata(self):
        """Load saved metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    saved_metadata = json.load(f)
                    self.cache_stages.update(saved_metadata.get('stages', {}))
                    self.priority_satellites = saved_metadata.get('priority_satellites', [])
                    self.metrics.update(saved_metadata.get('metrics', {}))
            except Exception as e:
                logger.error(f"Error loading cache metadata: {e}")

    def _save_metadata(self):
        """Save metadata with performance metrics"""
        try:
            metadata = {
                'stages': self.cache_stages,
                'priority_satellites': self.priority_satellites,
                'last_update': datetime.now(timezone.utc).isoformat(),
                'position_interval_seconds': self.position_interval_seconds,
                'metrics': self.metrics,
                'cache_stats': self.memory_cache.get_stats()
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache metadata: {e}")

    def cleanup_expired_cache(self):
        """Smart cleanup: Delete only PAST data, keep valid future cache"""
        logger.info("🧹 Smart cleanup: Removing only past/expired data...")

        now = datetime.now(timezone.utc)
        deleted_count = 0

        try:
            # Clean up stage files
            for stage in ['stage1', 'stage2', 'stage3', 'stage4']:
                if stage in self.cache_stages and 'end_time' in self.cache_stages[stage]:
                    end_time = datetime.fromisoformat(self.cache_stages[stage]['end_time'])

                    if end_time < now:
                        # Clean chunked data
                        stage_files = list(self.cache_dir.glob(f'{stage}_*.npz'))
                        for file in stage_files:
                            try:
                                file.unlink()
                                deleted_count += 1
                            except Exception as e:
                                logger.warning(f"Error deleting {file}: {e}")

                        if stage_files:
                            self.cache_stages[stage]['status'] = 'expired'
                            logger.info(f"✅ Deleted {len(stage_files)} expired files from {stage}")

            # Clean old pass predictions
            self.pass_cache.cleanup_old_passes(days_to_keep=7)

            # Clean on-demand cache
            for norad_id in list(self.on_demand_cache.keys()):
                cache_info = self.on_demand_cache[norad_id]
                cached_at = datetime.fromisoformat(cache_info['cached_at'])
                expires_at = cached_at + timedelta(hours=cache_info['duration_hours'])

                if expires_at < now:
                    del self.on_demand_cache[norad_id]
                    ondemand_files = list(self.cache_dir.glob(f'ondemand_*_{norad_id}_*.npz'))
                    for file in ondemand_files:
                        try:
                            file.unlink()
                            deleted_count += 1
                        except Exception:
                            pass

            if deleted_count > 0:
                logger.info(f"🗑️ Deleted {deleted_count} past/expired cache files")
                self.memory_cache.clear()
                self.chunked_store.chunk_cache.clear()
                self._save_metadata()
            else:
                logger.info("✅ No past/expired files to delete")

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

    def _identify_priority_satellites(self):
        """Identify priority satellites for caching"""
        all_sats = list(self.satellite_manager.satellites.keys())

        # Could implement smart filtering here based on:
        # - Satellite type (LEO, MEO, GEO)
        # - Usage frequency
        # - Object type (PAYLOAD vs DEBRIS)

        self.priority_satellites = all_sats
        logger.info(f"Caching ALL {len(self.priority_satellites)} satellites")

    def calculate_positions_for_satellites(self, satellite_ids: List[int],
                                          start_time: datetime,
                                          end_time: datetime,
                                          batch_size: int = 25) -> Dict:
        """
        Calculate satellite positions with RAM-FRIENDLY batching.

        Args:
            batch_size: Satellites per batch (25 for 8GB RAM, 10 for 4GB RAM)
        """
        total_satellites = len(satellite_ids)

        # If few satellites, process all at once
        if total_satellites <= batch_size:
            return self._calculate_positions_unbatched(satellite_ids, start_time, end_time)

        # Process in batches to avoid RAM exhaustion
        logger.info(f"🔄 RAM-FRIENDLY BATCHING: {total_satellites} satellites → {batch_size} per batch")
        positions_data = {}

        for batch_start in range(0, total_satellites, batch_size):
            batch_end = min(batch_start + batch_size, total_satellites)
            batch_ids = satellite_ids[batch_start:batch_end]
            batch_num = (batch_start // batch_size) + 1
            total_batches = (total_satellites + batch_size - 1) // batch_size

            logger.info(f"📦 Batch {batch_num}/{total_batches}: "
                       f"Satellites {batch_start+1}-{batch_end} ({len(batch_ids)} sats)")

            # Process this batch
            batch_data = self._calculate_positions_unbatched(batch_ids, start_time, end_time)
            positions_data.update(batch_data)

            logger.info(f"   ✓ Saved {len(batch_data)} satellites, clearing RAM...")

            # Force garbage collection to free RAM
            del batch_data
            gc.collect()

        logger.info(f"✅ All {total_batches} batches complete: {len(positions_data)} satellites")
        return positions_data

    def _calculate_positions_unbatched(self, satellite_ids: List[int],
                                       start_time: datetime,
                                       end_time: datetime) -> Dict:
        """Internal method: Calculate positions without batching (original logic)"""
        total_seconds = int((end_time - start_time).total_seconds())
        interval_seconds = 15
        num_intervals = total_seconds // interval_seconds

        positions_data = {}

        logger.debug(f"Calculating positions for {len(satellite_ids)} satellites")
        logger.debug(f"Time range: {start_time} to {end_time} ({total_seconds/3600:.1f} hours)")
        logger.debug(f"Intervals: {num_intervals} (every {interval_seconds} seconds)")

        # Parallel processing for better performance
        def calculate_satellite_positions(norad_id):
            if norad_id not in self.satellite_manager.satellites:
                return None

            try:
                sat_data = self.satellite_manager.satellites[norad_id]
                satellite = sat_data['satellite_obj']

                # Extract TLE metadata for tracking
                # Get TLE lines from satellite_manager's raw TLE data
                tle_line1 = getattr(satellite, 'line1', '')
                tle_line2 = getattr(satellite, 'line2', '')

                # If not found, create a unique hash from NORAD ID and epoch
                if not tle_line1 or not tle_line2:
                    tle_hash = hashlib.sha256(f"{norad_id}_{satellite.model.jdsatepoch}".encode()).hexdigest()
                else:
                    tle_hash = hashlib.sha256(f"{tle_line1}{tle_line2}".encode()).hexdigest()

                tle_epoch = satellite.model.jdsatepoch  # Julian day epoch from TLE

                # Calculate orbital elements from TLE
                orbital_elements = self._extract_orbital_elements(satellite)
                orbit_class = self._classify_orbit(orbital_elements['semi_major_axis'])

                # Calculate cache expiry (TLE valid for ~48 hours in cache)
                cache_expiry = (start_time + timedelta(days=2)).timestamp()

                # Pre-allocate arrays
                num_points = num_intervals + 1
                epochs = np.zeros(num_points, dtype=np.float64)
                timestamps = []
                latitudes = np.zeros(num_points, dtype=np.float32)
                longitudes = np.zeros(num_points, dtype=np.float32)
                altitudes = np.zeros(num_points, dtype=np.float32)
                # ECI state vector (canonical inertial frame for orbit rendering)
                eci_x = np.zeros(num_points, dtype=np.float64)
                eci_y = np.zeros(num_points, dtype=np.float64)
                eci_z = np.zeros(num_points, dtype=np.float64)
                eci_vx = np.zeros(num_points, dtype=np.float64)
                eci_vy = np.zeros(num_points, dtype=np.float64)
                eci_vz = np.zeros(num_points, dtype=np.float64)
                # ECEF frame (for ground station geometry only)
                ecef_x = np.zeros(num_points, dtype=np.float64)
                ecef_y = np.zeros(num_points, dtype=np.float64)
                ecef_z = np.zeros(num_points, dtype=np.float64)
                ecef_vx = np.zeros(num_points, dtype=np.float64)
                ecef_vy = np.zeros(num_points, dtype=np.float64)
                ecef_vz = np.zeros(num_points, dtype=np.float64)


                # Vectorized time generation
                time_points = [start_time + timedelta(seconds=i * interval_seconds) 
                              for i in range(num_points)]
                skyfield_times = self.satellite_manager.ts.from_datetimes(time_points)

                # Batch calculation
                for i in range(num_points):
                    t = time_points[i]
                    t_skyfield = skyfield_times[i] if hasattr(skyfield_times, '__getitem__') else self.satellite_manager.ts.from_datetime(t)

                    epochs[i] = t.timestamp()
                    timestamps.append(t.isoformat())

                    # Calculate position (geocentric = ECI-like frame)
                    geocentric = satellite.at(t_skyfield)
                    subpoint = wgs84.subpoint(geocentric)

                    latitudes[i] = float(subpoint.latitude.degrees)
                    longitudes[i] = float(subpoint.longitude.degrees)
                    altitudes[i] = float(subpoint.elevation.km)

                    # ECI position and velocity (km to meters)
                    position_km = geocentric.position.km
                    velocity_km_s = geocentric.velocity.km_per_s

                    eci_x[i] = float(position_km[0] * 1000.0)
                    eci_y[i] = float(position_km[1] * 1000.0)
                    eci_z[i] = float(position_km[2] * 1000.0)
                    eci_vx[i] = float(velocity_km_s[0] * 1000.0)
                    eci_vy[i] = float(velocity_km_s[1] * 1000.0)
                    eci_vz[i] = float(velocity_km_s[2] * 1000.0)

                    # ECEF position (Earth-fixed frame) - For ground station geometry
                    # Convert geodetic (lat/lon/alt) to ECEF Cartesian coordinates
                    lat_rad = np.radians(float(subpoint.latitude.degrees))
                    lon_rad = np.radians(float(subpoint.longitude.degrees))
                    alt_m = float(subpoint.elevation.m)
                    
                    # WGS84 ellipsoid parameters
                    a = 6378137.0  # semi-major axis (meters)
                    f = 1.0 / 298.257223563  # flattening
                    e2 = 2*f - f*f  # eccentricity squared
                    
                    # Radius of curvature in prime vertical
                    N = a / np.sqrt(1.0 - e2 * np.sin(lat_rad)**2)
                    
                    # ECEF coordinates
                    ecef_x[i] = float((N + alt_m) * np.cos(lat_rad) * np.cos(lon_rad))
                    ecef_y[i] = float((N + alt_m) * np.cos(lat_rad) * np.sin(lon_rad))
                    ecef_z[i] = float((N * (1 - e2) + alt_m) * np.sin(lat_rad))
                    
                    # ECEF velocity approximation (ECI velocity in ECEF frame)
                    # Note: This is simplified; proper conversion requires rotation matrix
                    ecef_vx[i] = float(velocity_km_s[0] * 1000.0)
                    ecef_vy[i] = float(velocity_km_s[1] * 1000.0)
                    ecef_vz[i] = float(velocity_km_s[2] * 1000.0)


                self.metrics['calculations_performed'] += num_points

                return norad_id, {
                    'name': sat_data['name'],
                    'epochs': epochs.tolist(),
                    'timestamps': timestamps,
                    'latitudes': latitudes.tolist(),
                    'longitudes': longitudes.tolist(),
                    'altitudes': altitudes.tolist(),
                    'eci_x': eci_x.tolist(),
                    'eci_y': eci_y.tolist(),
                    'eci_z': eci_z.tolist(),
                    'eci_vx': eci_vx.tolist(),
                    'eci_vy': eci_vy.tolist(),
                    'eci_vz': eci_vz.tolist(),
                    'ecef_x': ecef_x.tolist(),
                    'ecef_y': ecef_y.tolist(),
                    'ecef_z': ecef_z.tolist(),
                    'ecef_vx': ecef_vx.tolist(),
                    'ecef_vy': ecef_vy.tolist(),
                    'ecef_vz': ecef_vz.tolist(),
                    # Metadata
                    'tle_hash': tle_hash,
                    'tle_epoch': tle_epoch,
                    'semi_major_axis': orbital_elements['semi_major_axis'],
                    'eccentricity': orbital_elements['eccentricity'],
                    'inclination': orbital_elements['inclination'],
                    'raan': orbital_elements['raan'],
                    'arg_perigee': orbital_elements['arg_perigee'],
                    'mean_anomaly': orbital_elements['mean_anomaly'],
                    'orbital_period': orbital_elements['orbital_period'],
                    'orbit_class': orbit_class,
                    'cache_expiry': cache_expiry,
                    'is_continuous': True
                }

            except Exception as e:
                logger.warning(f"Error calculating positions for satellite {norad_id}: {e}")
                return None

        # Process satellites in parallel batches
        batch_size = 10
        successful = 0
        failed = 0

        for i in range(0, len(satellite_ids), batch_size):
            batch = satellite_ids[i:i+batch_size]
            futures = [self.executor.submit(calculate_satellite_positions, sat_id) 
                      for sat_id in batch]

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    norad_id, data = result
                    positions_data[norad_id] = data
                    successful += 1
                else:
                    failed += 1

            # Log progress every 50 satellites
            if (i + batch_size) % 50 == 0:
                logger.info(f"Progress: {i + batch_size}/{len(satellite_ids)} satellites processed ({successful} successful, {failed} failed)")

        logger.info(f"✅ Position calculation complete: {successful} successful, {failed} failed")
        return positions_data

    def save_satellite_cache(self, norad_id: int, positions_data: Dict, stage_name: str):
        """Save satellite data using chunked storage for efficiency"""
        try:
            data = positions_data[norad_id]
            self.chunked_store.save_chunked_data(norad_id, data, stage_name)
            return True
        except Exception as e:
            logger.error(f"Error saving cache for satellite {norad_id}: {e}")
            return False

    def load_satellite_cache(self, norad_id: int, stage_name: str, 
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> Optional[Dict]:
        """Load satellite cache with optional time range filtering"""
        cache_key = f"{stage_name}_{norad_id}"

        # Check memory cache first
        if start_time is None and end_time is None:
            cached = self.memory_cache.get(cache_key)
            if cached is not None:
                self.metrics['cache_hits'] += 1
                return cached

        self.metrics['cache_misses'] += 1

        # Determine time range
        if start_time is None:
            start_time = datetime.now(timezone.utc)
        if end_time is None:
            if 'stage1' in stage_name:
                end_time = start_time + timedelta(minutes=5)
            elif 'stage2' in stage_name:
                end_time = start_time + timedelta(hours=4)
            elif 'stage3' in stage_name:
                end_time = start_time.replace(hour=23, minute=59, second=59)
            else:
                end_time = start_time + timedelta(days=7)

        # Load from chunked storage
        data = self.chunked_store.load_chunked_data(norad_id, start_time, end_time, stage_name)

        # Validate loaded data
        if data:
            epochs = data.get('epochs')
            if epochs is None or len(epochs) == 0:
                logger.warning(f"Cache loaded but empty for satellite {norad_id} in {stage_name}")
                return None
            logger.debug(f"Successfully loaded {len(epochs)} cached positions for satellite {norad_id}")
        else:
            logger.debug(f"No cache data found for satellite {norad_id} in {stage_name}")

        if data and start_time is None and end_time is None:
            self.memory_cache.put(cache_key, data)

        return data

    def stage1_immediate_cache(self):
        """Stage 1: Cache 5 minutes of data immediately"""
        # STRICT VALIDATION: Check both metadata AND actual cache files
        with self.cache_lock:
            stage1_valid = False
            
            if self.cache_stages['stage1']['status'] == 'completed':
                end_time_str = self.cache_stages['stage1'].get('end_time')
                if end_time_str:
                    try:
                        end_time = datetime.fromisoformat(end_time_str)
                        now = datetime.now(timezone.utc)
                        
                        # CRITICAL: Verify actual cache files exist with correct count
                        cache_files = list(self.cache_dir.glob('stage1_*.npz'))
                        expected_min_files = len(self.priority_satellites) * 0.95  # 95% threshold
                        
                        # Validate: files exist, not expired, sufficient coverage
                        if (len(cache_files) >= expected_min_files and 
                            end_time > now and 
                            self.cache_stages['stage1'].get('satellite_count', 0) > 0):
                            
                            stage1_valid = True
                            logger.info(f"✅ Stage 1 VALIDATED: {len(cache_files)} files, {self.cache_stages['stage1']['satellite_count']} satellites")
                            logger.info(f"   Cache valid until: {end_time.isoformat()}")
                        else:
                            logger.warning(f"⚠️ Stage 1 INVALID: files={len(cache_files)}/{expected_min_files}, expired={end_time <= now}")
                    except Exception as e:
                        logger.warning(f"⚠️ Stage 1 validation error: {e}")
            
            # If Stage 1 is valid, proceed to Stage 2
            if stage1_valid:
                self.stage2_background_cache()
                return
        
        logger.info("🚀 Stage 1: Starting fresh cache calculation (5 minutes)...")

        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(minutes=5)

        positions_data = self.calculate_positions_for_satellites(
            self.priority_satellites, start_time, end_time
        )

        logger.info(f"💾 Saving {len(positions_data)} satellites to cache...")
        success_count = 0
        failed_count = 0

        for norad_id in positions_data.keys():
            if self.save_satellite_cache(norad_id, positions_data, 'stage1'):
                success_count += 1
            else:
                failed_count += 1

            # Log progress every 50 satellites
            if (success_count + failed_count) % 50 == 0:
                logger.info(f"Save progress: {success_count + failed_count}/{len(positions_data)} ({success_count} saved, {failed_count} failed)")

        logger.info(f"💾 Cache saving complete: {success_count} saved, {failed_count} failed")

        # Clear positions_data from RAM before proceeding
        del positions_data
        gc.collect()

        # Validate Stage 1 completion
        cache_files = list(self.cache_dir.glob('stage1_*.npz'))
        
        with self.cache_lock:
            self.cache_stages['stage1']['status'] = 'completed'
            self.cache_stages['stage1']['satellite_count'] = success_count
            self.cache_stages['stage1']['completed_at'] = datetime.now(timezone.utc).isoformat()
            self.cache_stages['stage1']['end_time'] = end_time.isoformat()
            self.cache_stages['stage1']['cache_files'] = len(cache_files)
            self._save_metadata()

        logger.info(f"✅ Stage 1 COMPLETE: {success_count} satellites, {len(cache_files)} cache files")
        logger.info(f"   Duration: 5 minutes, Valid until: {end_time.isoformat()}")
        logger.info(f"🔄 Proceeding to Stage 2...")

        # Start stage 2 in background
        self.stage2_background_cache()


    def validate_cache(self, norad_id: int, stage: str) -> Dict:
        """
        Validate cache integrity and expiry.
        Returns validation status including TLE hash match and expiry check.
        """
        try:
            # Load cached data
            now = datetime.now(timezone.utc)
            cached_data = self.load_satellite_cache(norad_id, stage, now, now + timedelta(minutes=5))

            if not cached_data:
                return {
                    'valid': False,
                    'reason': 'No cached data found',
                    'requires_refresh': True
                }

            # Check cache expiry
            cache_expiry = cached_data.get('cache_expiry')
            if cache_expiry:
                expiry_time = datetime.fromtimestamp(float(cache_expiry[0]), tz=timezone.utc)
                if now > expiry_time:
                    return {
                        'valid': False,
                        'reason': f'Cache expired at {expiry_time.isoformat()}',
                        'expired_at': expiry_time.isoformat(),
                        'requires_refresh': True
                    }

            # Check TLE hash match
            if norad_id in self.satellite_manager.satellites:
                sat = self.satellite_manager.satellites[norad_id]['satellite_obj']
                current_tle_hash = hashlib.sha256(
                    f"{sat.model.line1}{sat.model.line2}".encode()
                ).hexdigest()

                cached_tle_hash = cached_data.get('tle_hash')
                if cached_tle_hash and cached_tle_hash[0] != current_tle_hash:
                    return {
                        'valid': False,
                        'reason': 'TLE updated - cache invalidated',
                        'old_tle_hash': str(cached_tle_hash[0]),
                        'new_tle_hash': current_tle_hash,
                        'requires_refresh': True
                    }

            # Check chunk continuity
            is_continuous = cached_data.get('is_continuous')
            if is_continuous is not None and not is_continuous[0]:
                logger.warning(f"Cache for {norad_id} has discontinuities")

            # All checks passed
            return {
                'valid': True,
                'tle_hash': str(cached_data.get('tle_hash', [''])[0]),
                'orbit_class': str(cached_data.get('orbit_class', ['LEO'])[0]),
                'cache_created': datetime.fromtimestamp(
                    float(cached_data.get('cache_created', [0])[0]), 
                    tz=timezone.utc
                ).isoformat() if cached_data.get('cache_created') else None,
                'expiry': expiry_time.isoformat() if cache_expiry else None,
                'is_continuous': bool(is_continuous[0]) if is_continuous is not None else True,
                'requires_refresh': False
            }

        except Exception as e:
            logger.error(f"Error validating cache for {norad_id}: {e}")
            return {
                'valid': False,
                'reason': f'Validation error: {str(e)}',
                'requires_refresh': True
            }

    def stage2_background_cache(self):
        """Stage 2: Smart incremental caching (RAM-friendly)"""
        def run_stage2():
            # Initialize smart cache manager if not done
            if self.smart_cache is None:
                from smart_cache_manager import SmartCacheManager
                self.smart_cache = SmartCacheManager(self)
                logger.info("🧠 Smart cache manager initialized")

            # Use smart incremental update instead of rebuilding everything
            try:
                logger.info("🚀 Stage 2: Smart incremental update (only builds missing ranges)")
                self.smart_cache.smart_incremental_update()

                # Mark Stage 2 as complete
                with self.cache_lock:
                    self.cache_stages['stage2']['status'] = 'completed'
                    self.cache_stages['stage2']['completed_at'] = datetime.now(timezone.utc).isoformat()
                    self.cache_stages['stage2']['end_time'] = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
                    self._save_metadata()

                logger.info(f"✅ Stage 2 complete (smart incremental)")

                # Proceed to Stage 3 (which will also use smart update)
                self.stage3_background_cache()

            except Exception as e:
                logger.error(f"Error in Stage 2 smart update: {e}")
                import traceback
                traceback.print_exc()

                # Fallback to old method if smart update fails
                logger.warning("⚠️ Falling back to traditional cache method...")
                self._stage2_fallback()

        thread = threading.Thread(target=run_stage2, daemon=True)
        thread.start()
        self.background_threads.append(thread)

    def _stage2_fallback(self):
        """Fallback to old Stage 2 method if smart cache fails"""
        logger.info("📄 Stage 2 FALLBACK: Traditional cache calculation (4 hours)...")

        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=4)

        positions_data = self.calculate_positions_for_satellites(
            self.priority_satellites, start_time, end_time
        )

        success_count = 0
        for norad_id in positions_data.keys():
            if self.save_satellite_cache(norad_id, positions_data, 'stage2'):
                success_count += 1

        with self.cache_lock:
            self.cache_stages['stage2']['status'] = 'completed'
            self.cache_stages['stage2']['satellite_count'] = success_count
            self.cache_stages['stage2']['completed_at'] = datetime.now(timezone.utc).isoformat()
            self.cache_stages['stage2']['end_time'] = end_time.isoformat()
            self._save_metadata()

        logger.info(f"✅ Stage 2 FALLBACK COMPLETE: {success_count} satellites")
        self.stage3_background_cache()

    def stage3_background_cache(self):
        """Stage 3: Cache rest of day in background"""
        def run_stage3():
            # STRICT VALIDATION: Check both metadata AND actual cache files
            with self.cache_lock:
                stage3_valid = False
                
                if self.cache_stages['stage3']['status'] == 'completed':
                    end_time_str = self.cache_stages['stage3'].get('end_time')
                    if end_time_str:
                        try:
                            end_time = datetime.fromisoformat(end_time_str)
                            now = datetime.now(timezone.utc)
                            cache_files = list(self.cache_dir.glob('stage3_*.npz'))
                            expected_min_files = len(self.priority_satellites) * 0.95
                            
                            # Validate: files exist, not expired, sufficient coverage
                            if (len(cache_files) >= expected_min_files and 
                                end_time > now and
                                self.cache_stages['stage3'].get('satellite_count', 0) > 0):
                                
                                stage3_valid = True
                                logger.info(f"✅ Stage 3 VALIDATED: {len(cache_files)} files, {self.cache_stages['stage3']['satellite_count']} satellites")
                                logger.info(f"   Cache valid until: {end_time.isoformat()}")
                            else:
                                logger.warning(f"⚠️ Stage 3 INVALID: files={len(cache_files)}/{expected_min_files}, expired={end_time <= now}")
                        except Exception as e:
                            logger.warning(f"⚠️ Stage 3 validation error: {e}")
                
                # If Stage 3 is valid, proceed to Stage 4
                if stage3_valid:
                    self.stage4_background_cache()
                    return
            
            logger.info("📄 Stage 3: Starting fresh cache calculation (rest of day)...")

            start_time = datetime.now(timezone.utc)
            end_of_day = start_time.replace(hour=23, minute=59, second=59, microsecond=999999)

            if end_of_day <= start_time:
                logger.info("Already at end of day, skipping Stage 3")
                self.stage4_background_cache()
                return

            positions_data = self.calculate_positions_for_satellites(
                self.priority_satellites, start_time, end_of_day
            )

            success_count = 0
            for norad_id in positions_data.keys():
                if self.save_satellite_cache(norad_id, positions_data, 'stage3'):
                    success_count += 1

            # Validate Stage 3 completion
            cache_files = list(self.cache_dir.glob('stage3_*.npz'))
            
            with self.cache_lock:
                self.cache_stages['stage3']['status'] = 'completed'
                self.cache_stages['stage3']['satellite_count'] = success_count
                self.cache_stages['stage3']['completed_at'] = datetime.now(timezone.utc).isoformat()
                self.cache_stages['stage3']['end_time'] = end_of_day.isoformat()
                self.cache_stages['stage3']['cache_files'] = len(cache_files)
                self._save_metadata()

            logger.info(f"✅ Stage 3 COMPLETE: {success_count} satellites, {len(cache_files)} cache files")
            logger.info(f"   Duration: rest of day, Valid until: {end_of_day.isoformat()}")
            logger.info(f"🔄 Proceeding to Stage 4...")

            # Start stage 4
            self.stage4_background_cache()

        thread = threading.Thread(target=run_stage3, daemon=True)
        thread.start()
        self.background_threads.append(thread)

    def stage4_background_cache(self):
        """Stage 4: Cache 48 hours of data in background"""
        logger.info("📄 Stage 4: Starting fresh cache calculation (48 hours)...")

        def run_stage4():
            # STRICT VALIDATION: Check both metadata AND actual cache files
            with self.cache_lock:
                stage4_valid = False
                
                if self.cache_stages['stage4']['status'] == 'completed':
                    end_time_str = self.cache_stages['stage4'].get('end_time')
                    if end_time_str:
                        try:
                            end_time = datetime.fromisoformat(end_time_str)
                            now = datetime.now(timezone.utc)
                            cache_files = list(self.cache_dir.glob('stage4_*.npz'))
                            expected_min_files = len(self.priority_satellites) * 2 * 0.95  # 2 days worth
                            
                            # Validate: files exist, not expired, sufficient coverage
                            if (len(cache_files) >= expected_min_files and 
                                end_time > now and
                                self.cache_stages['stage4'].get('satellite_count', 0) > 0):
                                
                                stage4_valid = True
                                logger.info(f"✅ Stage 4 VALIDATED: {len(cache_files)} files, {self.cache_stages['stage4']['satellite_count']} satellites")
                                logger.info(f"   Cache valid until: {end_time.isoformat()}")
                            else:
                                logger.warning(f"⚠️ Stage 4 INVALID: files={len(cache_files)}/{expected_min_files}, expired={end_time <= now}")
                        except Exception as e:
                            logger.warning(f"⚠️ Stage 4 validation error: {e}")
                
                # If Stage 4 is already valid, skip recalculation
                if stage4_valid:
                    logger.info("✅ All cache stages validated and complete!")
                    return
            
            logger.info("📄 Stage 4: Starting fresh cache calculation (48 hours)...")

            start_time = datetime.now(timezone.utc)
            end_time = start_time + timedelta(days=2)

            # Process in daily chunks to avoid memory issues
            for day in range(2):
                day_start = start_time + timedelta(days=day)
                day_end = day_start + timedelta(days=1)

                logger.info(f"Processing day {day+1}/2: {day_start.date()}")

                positions_data = self.calculate_positions_for_satellites(
                    self.priority_satellites, day_start, day_end
                )

                for norad_id in positions_data.keys():
                    self.save_satellite_cache(norad_id, positions_data, 'stage4')

            # Validate Stage 4 completion
            cache_files = list(self.cache_dir.glob('stage4_*.npz'))
            
            self.run_stage4_cleanup(end_time, len(cache_files))
            logger.info(f"✅ Stage 4 complete: Cached {len(self.priority_satellites)} satellites for 48 hours")

        thread = threading.Thread(target=run_stage4, daemon=True)
        thread.start()
        self.background_threads.append(thread)

    def calculate_pass_predictions_cached_adaptive(self, norad_id: int, latitude: float,
                                                   longitude: float, start_time: datetime,
                                                   end_time: datetime, min_elevation: float = 10) -> List[Dict]:
        """
        Calculate pass predictions using ONLY cached positions - NO REAL-TIME FALLBACK.
        If cache is not available, returns empty list.
        """
        if norad_id not in self.satellite_manager.satellites:
            return []

        try:
            # CACHE-ONLY: Get cached positions with 10-second resolution
            positions = self.get_position_range(norad_id, start_time, end_time, interval_seconds=30)

            # Enhanced validation - check for None, empty list, or insufficient data
            if not positions or len(positions) < 2:
                # Need at least 2 positions to calculate a pass
                logger.debug(f"Insufficient cached positions for satellite {norad_id}: {len(positions) if positions else 0} positions")
                return []

            sat_data = self.satellite_manager.satellites[norad_id]
            passes = []
            in_pass = False
            pass_data = None

            for pos in positions:
                try:
                    # Calculate elevation from cached position using simple geometry
                    pos_time = datetime.fromisoformat(pos['timestamp'])
                    
                    # Use cached lat/lon/alt to calculate observer-relative geometry
                    sat_lat = pos['latitude']
                    sat_lon = pos['longitude']
                    sat_alt = pos['altitude']
                    
                    # Simple elevation calculation from cached data
                    # (avoiding real-time TLE propagation)
                    elevation, azimuth, distance = self._calculate_observer_geometry(
                        latitude, longitude, sat_lat, sat_lon, sat_alt
                    )

                    if elevation >= min_elevation:
                        if not in_pass:
                            in_pass = True
                            pass_data = {
                                'start_time': pos_time,
                                'start_azimuth': azimuth,
                                'max_elevation': elevation,
                                'max_elevation_time': pos_time,
                                'max_elevation_azimuth': azimuth,
                                'positions': []
                            }
                        else:
                            if elevation > pass_data['max_elevation']:
                                pass_data['max_elevation'] = elevation
                                pass_data['max_elevation_time'] = pos_time
                                pass_data['max_elevation_azimuth'] = azimuth

                        pass_data['positions'].append({
                            'time': pos_time.isoformat(),
                            'elevation': round(elevation, 2),
                            'azimuth': round(azimuth, 2),
                            'distance': round(distance, 1),
                            'latitude': sat_lat,
                            'longitude': sat_lon,
                            'altitude': sat_alt
                        })
                    else:
                        if in_pass:
                            pass_data['end_time'] = pos_time
                            pass_data['end_azimuth'] = azimuth
                            pass_data['duration_seconds'] = (
                                pass_data['end_time'] - pass_data['start_time']
                            ).total_seconds()

                            if pass_data['duration_seconds'] >= 10:  # At least 10 seconds
                                passes.append({
                                    'start': pass_data['start_time'].isoformat(),
                                    'end': pass_data['end_time'].isoformat(),
                                    'duration': round(pass_data['duration_seconds']),
                                    'max_elevation': round(pass_data['max_elevation'], 2),
                                    'max_elevation_time': pass_data['max_elevation_time'].isoformat(),
                                    'start_azimuth': round(pass_data['start_azimuth'], 2),
                                    'max_elevation_azimuth': round(pass_data['max_elevation_azimuth'], 2),
                                    'end_azimuth': round(pass_data['end_azimuth'], 2),
                                    'positions': pass_data['positions']
                                })

                            in_pass = False
                            pass_data = None
                            
                except Exception as e:
                    logger.debug(f"Error processing position for {norad_id}: {e}")
                    continue

            # Handle pass extending beyond window
            if in_pass and pass_data:
                pass_data['end_time'] = end_time
                pass_data['duration_seconds'] = (
                    pass_data['end_time'] - pass_data['start_time']
                ).total_seconds()

                if pass_data['duration_seconds'] >= 10:
                    passes.append({
                        'start': pass_data['start_time'].isoformat(),
                        'end': pass_data['end_time'].isoformat(),
                        'duration': round(pass_data['duration_seconds']),
                        'max_elevation': round(pass_data['max_elevation'], 2),
                        'max_elevation_time': pass_data['max_elevation_time'].isoformat(),
                        'start_azimuth': round(pass_data['start_azimuth'], 2),
                        'max_elevation_azimuth': round(pass_data['max_elevation_azimuth'], 2),
                        'positions': pass_data['positions']
                    })

            self.metrics['passes_calculated'] += len(passes)
            return passes

        except Exception as e:
            logger.error(f"Cache-only pass prediction failed for {norad_id}: {e}")
            return []

    def _calculate_observer_geometry(self, obs_lat, obs_lon, sat_lat, sat_lon, sat_alt_km):
        """
        Calculate elevation, azimuth, and distance from observer to satellite
        using ONLY cached position data - NO real-time TLE propagation.
        """
        import math
        
        # DEBUG: Log input values occasionally
        # logger.debug(f"Geometry check: obs({obs_lat}, {obs_lon}) sat({sat_lat}, {sat_lon}, {sat_alt_km})")
        
        # Convert to radians
        obs_lat_rad = math.radians(obs_lat)
        obs_lon_rad = math.radians(obs_lon)
        sat_lat_rad = math.radians(sat_lat)
        sat_lon_rad = math.radians(sat_lon)
        
        # Earth radius in km
        earth_radius = 6371.0
        
        # Convert satellite position to ECEF (Approximate using spherical Earth for speed)
        # Using a slightly more accurate flattening factor if needed, but spherical is usually fine for elevation logic
        # However, let's ensure we aren't losing the satellite if it's barely above horizon
        sat_radius = earth_radius + sat_alt_km
        
        # Geocentric coordinates
        sat_x = sat_radius * math.cos(sat_lat_rad) * math.cos(sat_lon_rad)
        sat_y = sat_radius * math.cos(sat_lat_rad) * math.sin(sat_lon_rad)
        sat_z = sat_radius * math.sin(sat_lat_rad)
        
        # Observer position (on surface)
        obs_x = earth_radius * math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
        obs_y = earth_radius * math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
        obs_z = earth_radius * math.sin(obs_lat_rad)
        
        # Vector from observer to satellite (Slant vector)
        dx = sat_x - obs_x
        dy = sat_y - obs_y
        dz = sat_z - obs_z
        
        # Slant range
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        
        # Unit vector normal to surface at observer (UP vector)
        up_x = obs_x / earth_radius
        up_y = obs_y / earth_radius
        up_z = obs_z / earth_radius
        
        # Dot product: cos(angle between UP and SLANT)
        # cos(zeta) = (dx*up_x + dy*up_y + dz*up_z) / distance
        # elevation = 90 - zeta => sin(elevation) = cos(zeta)
        sin_el = (dx * up_x + dy * up_y + dz * up_z) / distance
        
        # Clamp for safety
        sin_el = max(-1.0, min(1.0, sin_el))
        elevation = math.degrees(math.asin(sin_el))
        
        # Calculate azimuth (angle from north)
        north_x = -math.sin(obs_lat_rad) * math.cos(obs_lon_rad)
        north_y = -math.sin(obs_lat_rad) * math.sin(obs_lon_rad)
        north_z = math.cos(obs_lat_rad)
        
        east_x = -math.sin(obs_lon_rad)
        east_y = math.cos(obs_lon_rad)
        east_z = 0
        
        # Project onto horizontal plane
        east_component = dx * east_x + dy * east_y + dz * east_z
        north_component = dx * north_x + dy * north_y + dz * north_z
        
        # Azimuth calculation
        azimuth = math.degrees(math.atan2(east_component, north_component))
        if azimuth < 0:
            azimuth += 360
        
        return elevation, azimuth, distance

    def run_stage4_cleanup(self, end_time, cache_file_count=0):
        with self.cache_lock:
            self.cache_stages['stage4']['status'] = 'completed'
            self.cache_stages['stage4']['satellite_count'] = len(self.priority_satellites)
            self.cache_stages['stage4']['completed_at'] = datetime.now(timezone.utc).isoformat()
            self.cache_stages['stage4']['end_time'] = end_time.isoformat()
            self.cache_stages['stage4']['cache_files'] = cache_file_count
            self._save_metadata()

            logger.info(f"✅ Stage 4 COMPLETE: {len(self.priority_satellites)} satellites, {cache_file_count} cache files")
            logger.info(f"   Duration: 48 hours, Valid until: {end_time.isoformat()}")
            logger.info(f"🎉 FULL CACHE SYSTEM OPERATIONAL - All stages validated!")

    def cache_satellite_on_demand(self, norad_id: int, duration_hours: int = 24) -> bool:
        """Cache specific satellite on-demand"""
        logger.info(f"📦 On-demand caching for satellite {norad_id} ({duration_hours} hours)...")

        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=duration_hours)

        positions_data = self.calculate_positions_for_satellites(
            [norad_id], start_time, end_time
        )

        if norad_id in positions_data:
            stage_name = f'ondemand_{duration_hours}h'
            if self.save_satellite_cache(norad_id, positions_data, stage_name):
                self.on_demand_cache[norad_id] = {
                    'cached_at': start_time.isoformat(),
                    'duration_hours': duration_hours
                }
                logger.info(f"✅ On-demand cache created for satellite {norad_id}")
                return True

        return False

    def start_progressive_caching(self):
        """Start the progressive caching system"""
        logger.info("🎯 Starting optimized progressive caching system...")
        
        # Quick check: Do we have ANY valid cache?
        stage1_files = list(self.cache_dir.glob('stage1_*.npz'))
        stage2_files = list(self.cache_dir.glob('stage2_*.npz'))
        
        logger.info(f"📦 Found {len(stage1_files)} Stage 1 files, {len(stage2_files)} Stage 2 files")
        
        if len(stage1_files) > 100:  # Reasonable threshold
            logger.info("✅ Substantial cache already exists, validating before recalculation...")

        def run_initial_cache():
            self.cleanup_expired_cache()
            self.stage1_immediate_cache()

        thread = threading.Thread(target=run_initial_cache, daemon=True)
        thread.start()
        self.background_threads.append(thread)
        logger.info("✅ Background caching started")

    # ============================================================================
    # COORDINATE CONVERSIONS
    # ============================================================================

    def _eci_to_ecef(self, x_eci, y_eci, z_eci, epoch):
        """Convert ECI to ECEF coordinates accounting for Earth rotation

        Args:
            x_eci, y_eci, z_eci: ECI coordinates in km (scalar or array)
            epoch: Unix timestamp (scalar or array)

        Returns:
            x_ecef, y_ecef, z_ecef in km
        """
        # Calculate GMST (Greenwich Mean Sidereal Time)
        # Using simplified formula - good enough for satellite tracking

        # Ensure epoch is array for vectorized operations
        epoch_arr = np.atleast_1d(epoch)

        # Julian date calculation
        jd = 2440587.5 + epoch_arr / 86400.0  # Unix epoch to Julian Date

        # GMST in degrees (simplified formula)
        # More accurate formula would use IAU 2000/2006 precession-nutation
        t = (jd - 2451545.0) / 36525.0  # Julian centuries from J2000
        gmst_deg = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * t**2 - t**3 / 38710000.0
        gmst_deg = gmst_deg % 360.0
        gmst_rad = np.radians(gmst_deg)

        # Rotation matrix from ECI to ECEF (rotation around Z-axis by GMST)
        cos_gmst = np.cos(gmst_rad)
        sin_gmst = np.sin(gmst_rad)

        # Ensure coordinates are arrays
        x_eci_arr = np.atleast_1d(x_eci)
        y_eci_arr = np.atleast_1d(y_eci)
        z_eci_arr = np.atleast_1d(z_eci)

        # Apply rotation (vectorized for arrays)
        x_ecef = x_eci_arr * cos_gmst + y_eci_arr * sin_gmst
        y_ecef = -x_eci_arr * sin_gmst + y_eci_arr * cos_gmst
        z_ecef = z_eci_arr  # Z-axis unchanged

        return x_ecef, y_ecef, z_ecef

    def _ecef_to_geodetic(self, x, y, z):
        """Convert ECEF coordinates to geodetic (lat/lon/alt)

        Input: x, y, z in KILOMETERS
        Output: lat (deg), lon (deg), alt (km)
        """
        # WGS84 parameters
        a = 6378.137  # semi-major axis (km) - CHANGED FROM METERS
        f = 1.0 / 298.257223563  # flattening
        b = a * (1.0 - f)  # semi-minor axis
        e2 = 1.0 - (b**2 / a**2)  # first eccentricity squared

        # Vectorized operations - inputs are in KM
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        z = np.asarray(z, dtype=np.float64)

        # Longitude
        lon = np.arctan2(y, x)

        # Latitude (iterative refinement)
        p = np.sqrt(x**2 + y**2)
        lat = np.arctan2(z, p * (1.0 - e2))

        # Iterate for accuracy
        for _ in range(3):
            N = a / np.sqrt(1.0 - e2 * np.sin(lat)**2)
            lat = np.arctan2(z + e2 * N * np.sin(lat), p)

        # Altitude - using numerically stable formula that works at all latitudes
        N = a / np.sqrt(1.0 - e2 * np.sin(lat)**2)

        # Use the more stable formula: h = sqrt(x² + y² + z²) - sqrt(N² - N²*e²*sin²(lat))
        # But simplified to avoid numerical issues at poles:
        r = np.sqrt(x**2 + y**2 + z**2)  # Distance from Earth center

        # For high latitudes (|lat| > 60°), use direct calculation
        # For low latitudes, use the standard formula
        cos_lat = np.cos(lat)
        high_lat_mask = np.abs(lat) > np.radians(60)

        alt = np.zeros_like(lat)

        # High latitude formula (more stable)
        if np.any(high_lat_mask):
            alt[high_lat_mask] = r[high_lat_mask] - (a * (1 - e2 * np.sin(lat[high_lat_mask])**2))

        # Low latitude formula (original, more accurate)
        if np.any(~high_lat_mask):
            # Avoid division by zero
            cos_lat_safe = np.where(np.abs(cos_lat) > 1e-10, cos_lat, 1e-10)
            alt[~high_lat_mask] = p[~high_lat_mask] / cos_lat_safe[~high_lat_mask] - N[~high_lat_mask]

        # Convert to degrees (altitude already in km)
        lat_deg = np.degrees(lat)
        lon_deg = np.degrees(lon)
        alt_km = alt  # Already in km since we use km throughout

        return lat_deg, lon_deg, alt_km

    def _hermite_interpolate(self, t0, t1, p0, p1, v0, v1, t):
        """Cubic Hermite interpolation with positions and velocities"""
        # Vectorized implementation
        t0 = np.asarray(t0, dtype=np.float64)
        t1 = np.asarray(t1, dtype=np.float64)
        t = np.asarray(t, dtype=np.float64)

        h = t1 - t0

        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            s = np.where(h != 0, (t - t0) / h, 0)

        # Hermite basis functions
        h00 = 2*s**3 - 3*s**2 + 1
        h10 = s**3 - 2*s**2 + s
        h01 = -2*s**3 + 3*s**2
        h11 = s**3 - s**2

        # Interpolate
        result = h00 * p0 + h10 * h * v0 + h01 * p1 + h11 * h * v1

        return np.where(h != 0, result, p0)

    def _process_positions_from_cache(self, sat_cache, start_dt, end_dt, interval_seconds):
        """Helper to process and interpolate positions from a loaded cache object"""
        # Generate target epochs
        start_epoch = start_dt.timestamp()
        end_epoch = end_dt.timestamp()
        num_points = int((end_epoch - start_epoch) / interval_seconds) + 1
        target_epochs = np.linspace(start_epoch, end_epoch, num_points)

        epochs = sat_cache['epochs']
        positions = []

        # Vectorized processing in chunks
        CHUNK_SIZE = 10000
        for i in range(0, len(target_epochs), CHUNK_SIZE):
            chunk_epochs = target_epochs[i:i+CHUNK_SIZE]

            # Find indices for interpolation
            indices = np.searchsorted(epochs, chunk_epochs)
            indices = np.clip(indices, 1, len(epochs) - 1)

            idx_before = indices - 1
            idx_after = indices

            # Hermite interpolation using ECI coordinates
            if sat_cache.get('eci_x') is not None and sat_cache.get('eci_vx') is not None:
                x_chunk = self._hermite_interpolate(
                    epochs[idx_before], epochs[idx_after],
                    sat_cache['eci_x'][idx_before], sat_cache['eci_x'][idx_after],
                    sat_cache['eci_vx'][idx_before], sat_cache['eci_vx'][idx_after],
                    chunk_epochs
                )
                y_chunk = self._hermite_interpolate(
                    epochs[idx_before], epochs[idx_after],
                    sat_cache['eci_y'][idx_before], sat_cache['eci_y'][idx_after],
                    sat_cache['eci_vy'][idx_before], sat_cache['eci_vy'][idx_after],
                    chunk_epochs
                )
                z_chunk = self._hermite_interpolate(
                    epochs[idx_before], epochs[idx_after],
                    sat_cache['eci_z'][idx_before], sat_cache['eci_z'][idx_after],
                    sat_cache['eci_vz'][idx_before], sat_cache['eci_vz'][idx_after],
                    chunk_epochs
                )

                # CRITICAL FIX: Cache stores ECI in METERS, convert to KM
                x_chunk_km = x_chunk / 1000.0
                y_chunk_km = y_chunk / 1000.0
                z_chunk_km = z_chunk / 1000.0

                # Convert ECI → ECEF → Geodetic (accounting for Earth rotation)
                x_ecef, y_ecef, z_ecef = self._eci_to_ecef(x_chunk_km, y_chunk_km, z_chunk_km, chunk_epochs)
                lats, lons, alts = self._ecef_to_geodetic(x_ecef, y_ecef, z_ecef)

                # Build position list
                for j, epoch in enumerate(chunk_epochs):
                    dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
                    positions.append({
                        'timestamp': dt.isoformat(),
                        'latitude': float(lats[j]) if hasattr(lats, '__getitem__') else float(lats),
                        'longitude': float(lons[j]) if hasattr(lons, '__getitem__') else float(lons),
                        'altitude': float(alts[j]) if hasattr(alts, '__getitem__') else float(alts),
                    })
            elif sat_cache.get('latitudes') is not None:
                # Fallback to linear interpolation
                dt_vals = epochs[idx_after] - epochs[idx_before]
                ratio = np.zeros_like(chunk_epochs)
                mask = dt_vals > 1e-6
                ratio[mask] = (chunk_epochs[mask] - epochs[idx_before][mask]) / dt_vals[mask]
                
                lats = sat_cache['latitudes'][idx_before] + ratio * (sat_cache['latitudes'][idx_after] - sat_cache['latitudes'][idx_before])
                lons = sat_cache['longitudes'][idx_before] + ratio * (sat_cache['longitudes'][idx_after] - sat_cache['longitudes'][idx_before])
                alts = sat_cache['altitudes'][idx_before] + ratio * (sat_cache['altitudes'][idx_after] - sat_cache['altitudes'][idx_before])
                
                for j, epoch in enumerate(chunk_epochs):
                    dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
                    positions.append({
                        'timestamp': dt.isoformat(),
                        'latitude': float(lats[j]),
                        'longitude': float(lons[j]),
                        'altitude': float(alts[j]),
                    })

        return positions

    # ============================================================================
    # OPTIMIZED POSITION LOOKUP
    # ============================================================================

    def get_cached_position(self, norad_id: int, target_time: datetime) -> Optional[Dict]:
        """Get interpolated satellite position at target_time"""
        # Ensure timezone-aware
        if isinstance(target_time, str):
            target_dt = datetime.fromisoformat(target_time)
        else:
            target_dt = target_time

        if target_dt.tzinfo is None:
            target_dt = target_dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        time_diff = (target_dt - now).total_seconds()

        # Determine stage
        if -300 <= time_diff <= 300:
            stage = 'stage1'
        elif time_diff <= 14400:
            stage = 'stage2'
        elif target_dt.date() == now.date():
            stage = 'stage3'
        else:
            stage = 'stage4'

        # Load appropriate cache
        sat_cache = self.load_satellite_cache(
            norad_id, stage,
            target_dt - timedelta(minutes=1),
            target_dt + timedelta(minutes=1)
        )

        if sat_cache is None:
            # Try on-demand cache
            for hours in [24, 48]:
                sat_cache = self.load_satellite_cache(
                    norad_id, f'ondemand_{hours}h',
                    target_dt - timedelta(minutes=1),
                    target_dt + timedelta(minutes=1)
                )
                if sat_cache:
                    break

        if not sat_cache or sat_cache['epochs'] is None or len(sat_cache['epochs']) == 0:
            return None

        target_epoch = target_dt.timestamp()
        epochs = sat_cache['epochs']

        # Binary search for closest epochs
        idx = np.searchsorted(epochs, target_epoch)

        if idx == 0:
            idx = 1
        elif idx >= len(epochs):
            idx = len(epochs) - 1

        idx_before = idx - 1
        idx_after = min(idx, len(epochs) - 1)

        self.metrics['interpolations_performed'] += 1

        # Hermite interpolation for smooth, accurate results
        if (sat_cache['eci_x'] is not None and 
            sat_cache['eci_vx'] is not None):

            x = self._hermite_interpolate(
                epochs[idx_before], epochs[idx_after],
                sat_cache['eci_x'][idx_before], sat_cache['eci_x'][idx_after],
                sat_cache['eci_vx'][idx_before], sat_cache['eci_vx'][idx_after],
                target_epoch
            )
            y = self._hermite_interpolate(
                epochs[idx_before], epochs[idx_after],
                sat_cache['eci_y'][idx_before], sat_cache['eci_y'][idx_after],
                sat_cache['eci_vy'][idx_before], sat_cache['eci_vy'][idx_after],
                target_epoch
            )
            z = self._hermite_interpolate(
                epochs[idx_before], epochs[idx_after],
                sat_cache['eci_z'][idx_before], sat_cache['eci_z'][idx_after],
                sat_cache['eci_vz'][idx_before], sat_cache['eci_vz'][idx_after],
                target_epoch
            )

            # CRITICAL FIX: Cache stores ECI in METERS, convert to KM
            x_km = x / 1000.0
            y_km = y / 1000.0
            z_km = z / 1000.0

            # Convert ECI → ECEF → Geodetic (accounting for Earth rotation)
            x_ecef, y_ecef, z_ecef = self._eci_to_ecef(x_km, y_km, z_km, target_epoch)
            lat, lon, alt = self._ecef_to_geodetic(x_ecef, y_ecef, z_ecef)

            # Ensure all values are Python primitives, not numpy types
            return {
                'timestamp': target_dt.isoformat(),
                'latitude': float(lat.item() if hasattr(lat, 'item') else lat),
                'longitude': float(lon.item() if hasattr(lon, 'item') else lon),
                'altitude': float(alt.item() if hasattr(alt, 'item') else alt),
                'name': str(sat_cache.get('name', ['Unknown'])[0] if isinstance(sat_cache.get('name'), np.ndarray) else sat_cache.get('name', 'Unknown')),
                # Include ECI coordinates for visualization
                'eci_x': float(x.item() if hasattr(x, 'item') else x),
                'eci_y': float(y.item() if hasattr(y, 'item') else y),
                'eci_z': float(z.item() if hasattr(z, 'item') else z),
            }

        # Fallback to direct lat/lon interpolation (less accurate)
        if sat_cache['latitudes'] is not None:
            ratio = (target_epoch - epochs[idx_before]) / (epochs[idx_after] - epochs[idx_before])

            lat = sat_cache['latitudes'][idx_before] + ratio * (
                sat_cache['latitudes'][idx_after] - sat_cache['latitudes'][idx_before]
            )
            lon = sat_cache['longitudes'][idx_before] + ratio * (
                sat_cache['longitudes'][idx_after] - sat_cache['longitudes'][idx_before]
            )
            alt = sat_cache['altitudes'][idx_before] + ratio * (
                sat_cache['altitudes'][idx_after] - sat_cache['altitudes'][idx_before]
            )

            # Ensure all values are Python primitives, not numpy types
            return {
                'timestamp': target_dt.isoformat(),
                'latitude': float(lat),
                'longitude': float(lon),
                'altitude': float(alt),
                'name': str(sat_cache.get('name', ['Unknown'])[0] if isinstance(sat_cache.get('name'), np.ndarray) else sat_cache.get('name', 'Unknown'))
            }

        return None

    def get_position_range(self, norad_id: int, start_time: datetime, 
                          end_time: datetime, interval_seconds: int = 1) -> Optional[List[Dict]]:
        """Get interpolated positions over a time range by merging multiple cache stages if necessary"""
        # Ensure timezone-aware
        if isinstance(start_time, str):
            start_dt = datetime.fromisoformat(start_time)
        else:
            start_dt = start_time

        if isinstance(end_time, str):
            end_dt = datetime.fromisoformat(end_time)
        else:
            end_dt = end_time

        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)

        # For pass prediction over long ranges (like 48h), we should try to get data from ANY available cache
        # that covers the start of the window, or better yet, try all stages.
        all_positions = []
        
        # Try stages in order of duration/depth
        # Stage 4 is most likely to cover a 48h window if it exists
        # Stage 3 covers rest of today
        # Stage 2 covers next 4 hours
        # Stage 1 covers next 5 mins
        
        found_cache = False
        # Try sliding window cache first (48-hour coverage), then regular stages
        for stage in ['sliding', 'stage4', 'stage3', 'stage2', 'stage1']:
            sat_cache = self.load_satellite_cache(norad_id, stage, start_dt, end_dt)
            if sat_cache and sat_cache.get('epochs') is not None and len(sat_cache['epochs']) >= 2:
                # We found a cache that covers at least part of the range
                # Use a small buffer to avoid edge issues
                cache_start = sat_cache['epochs'][0]
                cache_end = sat_cache['epochs'][-1]
                
                # Check if this cache covers the START of our requested range
                # This is crucial for pass prediction to work correctly
                if cache_start <= start_dt.timestamp() + 300: # 5 min buffer
                    positions = self._process_positions_from_cache(sat_cache, start_dt, end_dt, interval_seconds)
                    if positions:
                        return positions
        
        # Try on-demand caches as final fallback
        for hours in [48, 24]:
            sat_cache = self.load_satellite_cache(norad_id, f'ondemand_{hours}h', start_dt, end_dt)
            if sat_cache and sat_cache.get('epochs') is not None and len(sat_cache['epochs']) >= 2:
                positions = self._process_positions_from_cache(sat_cache, start_dt, end_dt, interval_seconds)
                if positions:
                    return positions

        return None

    # ============================================================================
    # AI AGENT QUERY INTERFACE
    # ============================================================================

    def get_cache_status(self) -> Dict:
        """Get comprehensive cache system status"""
        cached_files = list(self.cache_dir.glob('*.npz'))
        pass_files = list((self.cache_dir / 'passes').glob('*.json'))

        return {
            'stages': self.cache_stages,
            'priority_satellites': len(self.priority_satellites),
            'cached_files': len(cached_files),
            'pass_cache_files': len(pass_files),
            'cache_directory': str(self.cache_dir),
            'position_interval_seconds': self.position_interval_seconds,
            'active_threads': len([t for t in self.background_threads if t.is_alive()]),
            'on_demand_cached': len(self.on_demand_cache),
            'memory_cache': self.memory_cache.get_stats(),
            'chunk_cache': self.chunked_store.chunk_cache.get_stats(),
            'performance_metrics': self.metrics
        }

    def shutdown(self):
        """Graceful shutdown of the cache manager"""
        logger.info("Shutting down cache manager...")

        # Save final metadata
        self._save_metadata()

        # Shutdown executor
        self.executor.shutdown(wait=True)

        # Wait for background threads
        for thread in self.background_threads:
            if thread.is_alive():
                thread.join(timeout=5)

        logger.info("Cache manager shutdown complete")