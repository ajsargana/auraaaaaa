"""
Rebuild Sliding Window Cache

This script rebuilds the 7-day sliding window cache from scratch.
Use this after fixing bugs in the sliding window or position cache code.
"""

import sys
import logging
from satellite_data_simple import SatelliteDataManager
from position_cache_manager_optimized import OptimizedPositionCacheManager
from sliding_window_cache import SlidingWindowCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("\n" + "="*70)
    print("SLIDING WINDOW CACHE REBUILD")
    print("="*70 + "\n")

    # Step 1: Load satellite data
    print("[1/3] Loading satellite data...")
    satellite_manager = SatelliteDataManager()
    if not satellite_manager.load_tle_data():
        print("[ERROR] Failed to load TLE data")
        return False

    satellite_count = len(satellite_manager.satellites)
    print(f"[OK] Loaded {satellite_count} satellites\n")

    # Step 2: Initialize position cache
    print("[2/3] Initializing position cache manager...")
    position_cache = OptimizedPositionCacheManager(satellite_manager)
    satellite_manager.set_position_cache_manager(position_cache)
    print("[OK] Position cache manager ready\n")

    # Step 3: Build sliding window cache
    print("[3/3] Building 7-day sliding window cache...")
    print("[INFO] This will take 1-2 hours depending on your system")
    print("[INFO] Progress will be shown every 2 hours built")
    print()

    sliding_cache = SlidingWindowCache(position_cache)

    try:
        success = sliding_cache.initial_build()

        if success:
            print("\n" + "="*70)
            print("CACHE BUILD COMPLETE!")
            print("="*70)
            print("The 7-day cache is now ready.")
            print("Next step: Rebuild the spatial index with rebuild_spatial_index.py")
            print("="*70 + "\n")
            return True
        else:
            print("\n[ERROR] Cache build failed")
            return False

    except Exception as e:
        print(f"\n[ERROR] Failed to build cache: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
