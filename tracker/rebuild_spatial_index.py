"""
Rebuild Spatial-Temporal Index

This script rebuilds the spatial-temporal index using disk-based storage.
Low RAM usage (~500MB) with incremental progress saving.
Can be stopped and resumed.
"""

import sys
import gc
import logging
from datetime import datetime, timezone
from satellite_data_simple import SatelliteDataManager
from position_cache_manager_optimized import OptimizedPositionCacheManager
from spatial_index_disk import DiskSpatialIndex

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("\n" + "="*70)
    print("SPATIAL-TEMPORAL INDEX REBUILD")
    print("="*70 + "\n")

    # Step 1: Load satellite data
    print("[1/4] Loading satellite data...")
    satellite_manager = SatelliteDataManager()
    if not satellite_manager.load_tle_data():
        print("[ERROR] Failed to load TLE data")
        return False

    satellite_count = len(satellite_manager.satellites)
    print(f"[OK] Loaded {satellite_count} satellites\n")

    # Step 2: Initialize position cache
    print("[2/4] Initializing position cache manager...")
    position_cache = OptimizedPositionCacheManager(satellite_manager)
    satellite_manager.set_position_cache_manager(position_cache)
    print("[OK] Position cache manager ready\n")

    # Step 3: Create new spatial index
    print("[3/4] Creating disk-based spatial index...")
    spatial_index = DiskSpatialIndex(
        db_path="cache/spatial_index.db",
        grid_size=5.0,
        time_bucket_minutes=1
    )
    print("[OK] Index object created\n")

    # Step 4: Build the index
    print("[4/4] Building spatial index incrementally...")
    print("[INFO] Using 48-hour time window")
    print("[INFO] Grid size: 5° (approx 550km at equator)")
    print("[INFO] Time buckets: 1 minute resolution")
    print("[INFO] Minimum elevation: 10°")
    print("[INFO] Batch size: 10 satellites (low RAM usage)")
    print("[INFO] Progress is saved - you can stop and resume anytime")
    print()

    # Option to clear previous progress
    import os
    if os.path.exists("cache/spatial_index.db"):
        response = input("Clear previous progress and start fresh? (y/N): ")
        if response.lower() == 'y':
            spatial_index.clear_progress()
            print("[OK] Cleared previous progress\n")

    try:
        spatial_index.build_index_incremental(
            position_cache_manager=position_cache,
            time_window_hours=48,  # 48 hours (matches cache)
            min_elevation=10.0,
            batch_size=10  # Process 10 satellites at a time
        )

        # Get stats
        stats = spatial_index.get_stats()
        metadata = stats['metadata']

        print("\n" + "="*70)
        print("INDEX BUILD COMPLETE!")
        print("="*70)
        print(f"Total entries: {metadata['total_entries']:,}")
        print(f"Satellites indexed: {metadata['satellite_count']:,}")
        if 'grid_cells_populated' in metadata:
            print(f"Grid cells populated: {metadata['grid_cells_populated']:,}")
        print(f"Time range: {metadata['time_range_start']} to {metadata['time_range_end']}")
        print(f"Memory estimate: {stats['memory_estimate_mb']:.1f} MB")
        print("="*70 + "\n")

        if metadata['total_entries'] == 0:
            print("[WARNING] Index has 0 entries! This means:")
            print("  - Position cache may not have data")
            print("  - Check cache/sliding_window_metadata.json")
            print("  - Run sliding_window_cache rebuild if needed")
            return False

        print("[SUCCESS] Spatial index rebuilt successfully!")
        print("[NOTE] Restart the Flask app to use the new index")
        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to build index: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
