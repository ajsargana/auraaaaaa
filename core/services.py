"""
Application Services Singleton
Replaces Flask app.py module-level initialization.
All managers are lazily initialized on first access.
"""
import os
import sys
import logging
import threading
import time

logger = logging.getLogger(__name__)

# Add tracker app to path so its modules can import each other
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TRACKER_DIR = os.path.join(_BASE_DIR, 'tracker')
_NASA_DIR = os.path.join(_BASE_DIR, 'nasa')
_LAUNCHES_DIR = os.path.join(_BASE_DIR, 'launches')
_AIRPLANES_DIR = os.path.join(_BASE_DIR, 'airplanes')
_CORE_DIR = os.path.join(_BASE_DIR, 'core')
_DATA_DIR = os.path.join(_CORE_DIR, 'data')

for _d in [_TRACKER_DIR, _NASA_DIR, _LAUNCHES_DIR, _AIRPLANES_DIR, _CORE_DIR]:
    if _d not in sys.path:
        sys.path.insert(0, _d)


class AppServices:
    """Thread-safe singleton holding all application service instances."""
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return

            from dotenv import load_dotenv
            load_dotenv(os.path.join(_BASE_DIR, '.env'))
            # Also try source .env
            source_env = os.path.join(
                _BASE_DIR, 'source', 'Sat-Track3zip', 'Sat-Track_latest', '.env'
            )
            if os.path.exists(source_env):
                load_dotenv(source_env)

            logger.info(f"NASA_API_KEY loaded: {'Yes' if os.environ.get('NASA_API_KEY') else 'No'}")
            logger.info(f"GEMINI_API_KEY loaded: {'Yes' if os.environ.get('GEMINI_API_KEY') else 'No'}")
            logger.info(f"OPENWEATHER_API_KEY loaded: {'Yes' if os.environ.get('OPENWEATHER_API_KEY') else 'No'}")

            self.satellite_manager = None
            self.position_cache = None
            self.spatial_index = None
            self.airplane_manager = None
            self.nasa_apod_module = None
            self.nasa_asteroids_module = None
            self.nasa_donki_module = None
            self.nasa_eonet_module = None
            self.launch_data_module = None
            self.eo_database = None
            self.fov_db = None           # EarthObservationSatellites singleton
            self.coverage_calculator = None

            self._do_init()
            self._initialized = True

    # ------------------------------------------------------------------
    def _do_init(self):
        """Heavy initialization — mirrors the top of the original app.py."""
        # --- Satellite Manager ---
        print("[SAT]  Initializing Satellite Data Manager...")
        from satellite_data_simple import SatelliteDataManager
        self.satellite_manager = SatelliteDataManager()

        # --- Airplane Manager ---
        print("  Initializing Airplane Data Manager...")
        from airplane_data import AirplaneDataManager
        self.airplane_manager = AirplaneDataManager()

        # --- NASA APOD ---
        print("[START] Initializing NASA APOD Module...")
        from nasa_apod_module import NASAAPODModule
        self.nasa_apod_module = NASAAPODModule()

        # --- NASA Asteroids ---
        print(" Initializing NASA Asteroids Module...")
        try:
            from nasa_asteroids_module import NASAAsteroidsModule
            self.nasa_asteroids_module = NASAAsteroidsModule()
            print("[OK] NASA Asteroids module initialized successfully!")
        except Exception as e:
            print(f"[ERR] Failed to initialize NASA Asteroids module: {e}")

        # --- NASA DONKI ---
        print(" Initializing NASA DONKI Module...")
        try:
            from donki_module import DONKIModule
            self.nasa_donki_module = DONKIModule()
            print("[OK] NASA DONKI module initialized successfully!")
        except Exception as e:
            print(f"[ERR] Failed to initialize NASA DONKI module: {e}")

        # --- NASA EONET ---
        print(" Initializing NASA EONET Module...")
        try:
            from nasa_eonet_module import NASAEONETModule
            self.nasa_eonet_module = NASAEONETModule()
            print("[OK] NASA EONET module initialized successfully!")
        except Exception as e:
            print(f"[ERR] Failed to initialize NASA EONET module: {e}")

        # --- Launch Data ---
        print("[START] Initializing Launch Data Module...")
        try:
            from launch_data_module import LaunchDataModule
            self.launch_data_module = LaunchDataModule()
            print("[OK] Launch Data module initialized successfully!")
        except Exception as e:
            print(f"[ERR] Failed to initialize Launch Data module: {e}")

        # --- Load TLE data ---
        print(" Loading satellite data...")
        if self.satellite_manager.load_tle_data():
            print("[OK] Satellite data loaded successfully!")
            satellites = self.satellite_manager.get_satellite_data()
            print(f"[INFO] Total satellites: {len(satellites)}")

            # Initialize AI chat
            from core.ai_chat_module import initialize_ai_system
            initialize_ai_system(self.satellite_manager)
            print(" AI chat system initialized with satellite database")

            # FOV Database (EarthObservationSatellites) — cached singleton
            print("[EO] Initializing Earth Observation FOV Database...")
            from tracker.satellite_fov_data import EarthObservationSatellites
            self.fov_db = EarthObservationSatellites()
            print(f"[OK] FOV database loaded ({len(self.fov_db.satellites)} satellites)")

            # EO Database
            print("[EO] Initializing Earth Observation Satellite Database...")
            from eo_satellite_database import EOSatelliteDatabase
            eo_json = os.path.join(_DATA_DIR, 'eo_satellites.json')
            if not os.path.exists(eo_json):
                eo_json = 'eo_satellites.json'
            self.eo_database = EOSatelliteDatabase(eo_json)

            if len(self.eo_database.satellites) == 0:
                print("[EO] No EO satellites found, initializing defaults...")
                self.eo_database.initialize_default_satellites()
            else:
                print(f"[OK] Loaded {len(self.eo_database.satellites)} EO satellite configurations")

            # Coverage Calculator
            print("[COVERAGE] Initializing 3D Globe-Accurate Coverage Calculator...")
            from satellite_coverage_3d import GlobeAccurateCoverageCalculator
            self.coverage_calculator = GlobeAccurateCoverageCalculator(
                self.satellite_manager, self.eo_database
            )
            print("[OK] Coverage calculator using geodesic geometry for 3D globe accuracy")
        else:
            print("[ERR] Failed to load satellite data")

        # --- Position cache ---
        if len(self.satellite_manager.satellites) > 0:
            self._initialize_position_cache()
        else:
            print("[WARN] Satellite manager has no satellites, will initialize cache after TLE load")

        # --- TLE update check ---
        logger.info("Checking TLE data freshness...")
        try:
            self.satellite_manager.tle_updater.update_if_needed()
        except Exception as e:
            logger.warning(f"TLE update check failed, will use existing data: {e}")

        logger.info("Satellite data will be loaded on first API request")

    # ------------------------------------------------------------------
    def _initialize_position_cache(self):
        if len(self.satellite_manager.satellites) > 0:
            print("[CACHE] Initializing Smart Sliding Window Cache Manager...")
            try:
                from position_cache_manager_optimized import OptimizedPositionCacheManager
                self.position_cache = OptimizedPositionCacheManager(self.satellite_manager)
                print(f"[OK] Position cache object created: {self.position_cache is not None}")

                self.satellite_manager.set_position_cache_manager(self.position_cache)
                print("[OK] Position cache connected to satellite manager")

                from sliding_window_cache import SlidingWindowCache
                sliding_cache = SlidingWindowCache(self.position_cache)

                svc = self  # capture for thread

                def start_sliding_cache_background():
                    time.sleep(5)
                    print("\n[START] Initializing 48-hour sliding window cache...")

                    if not sliding_cache.is_initialized:
                        print("[INFO] First run detected - building complete 48-hour cache")
                        print("[INFO] This will take about 1 hour, but only happens once!")
                        sliding_cache.initial_build()
                        print("\n[INDEX] Initial cache complete, building spatial index...")
                        svc._build_spatial_index()
                    else:
                        print("[INFO] Cache already initialized, checking for updates...")
                        if sliding_cache.needs_update():
                            sliding_cache.sliding_update()
                        if svc.spatial_index is None:
                            print("[INDEX] Building spatial index from existing cache...")
                            svc._build_spatial_index()

                    import schedule

                    def scheduled_slide():
                        print(f"\n[SCHEDULED] Running maintenance update...")
                        sliding_cache.sliding_update()

                    schedule.every(1.5).hours.do(scheduled_slide)

                    import time as time_module
                    while True:
                        schedule.run_pending()
                        time_module.sleep(60)

                cache_thread = threading.Thread(target=start_sliding_cache_background, daemon=True)
                cache_thread.start()
                print("[OK] Sliding window cache initialized (building in background)")
            except Exception as e:
                print(f"[ERR] Failed to initialize cache: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[WARN] No satellites loaded, skipping cache initialization")

    # ------------------------------------------------------------------
    def _build_spatial_index(self):
        if not self.position_cache:
            print("[WARN] Position cache not ready, cannot build spatial index")
            return
        try:
            from spatial_index_disk import DiskSpatialIndex

            print("[BUILD] Building disk-based spatial index (low RAM usage)...")
            self.spatial_index = DiskSpatialIndex(
                db_path="cache/spatial_index.db",
                grid_size=5.0,
                time_bucket_minutes=1,
            )

            if self.spatial_index.is_ready():
                stats = self.spatial_index.get_stats()
                entry_count = stats.get("entry_count", 0)
                if entry_count > 0:
                    print(f"[OK] Spatial index already exists with {entry_count:,} entries")
                    return

            self.spatial_index.build_index_incremental(
                position_cache_manager=self.position_cache,
                time_window_hours=48,
                min_elevation=10.0,
                batch_size=10,
            )
            print("[OK] Spatial-temporal index ready for ultra-fast queries!")
        except Exception as e:
            print(f"[ERR] Failed to build spatial index: {e}")
            import traceback
            traceback.print_exc()


def get_services() -> AppServices:
    """Return the global AppServices singleton."""
    return AppServices()
