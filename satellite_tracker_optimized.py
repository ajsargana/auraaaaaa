"""
Optimized satellite tracker with local caching and smooth movement
Simplified structure with separated concerns for better performance
"""

import logging
from datetime import datetime
from cache_manager import CacheManager
from satellite_categories import SatelliteCategories  
from satellite_data import SatelliteData
from offline_satellite_data import get_offline_tle_data

class SatelliteTrackerOptimized:
    def __init__(self, offline_mode=False):
        self.offline_mode = offline_mode
        self.cache_manager = CacheManager()
        self.categories_manager = SatelliteCategories()
        self.satellite_data = SatelliteData(self.categories_manager)
        
        # Initialize data
        self.load_satellite_data()
        
    def load_satellite_data(self):
        """Load satellite data with intelligent caching"""
        logging.info("Loading satellite data...")
        
        # Try to get fresh data if online and cache needs update
        if not self.offline_mode and self.cache_manager.needs_update():
            logging.info("Updating TLE cache from online sources...")
            if self.cache_manager.update_tle_cache():
                tle_data = self.cache_manager.get_cached_tle_data()
                if tle_data:
                    self.satellite_data.parse_tle_data(tle_data)
                    logging.info("Loaded fresh satellite data from cache")
                    return
        
        # Use cached data if available
        if self.cache_manager.has_cached_data():
            logging.info("Loading satellite data from cache...")
            tle_data = self.cache_manager.get_cached_tle_data()
            if tle_data:
                self.satellite_data.parse_tle_data(tle_data)
                logging.info("Loaded satellite data from cache")
                return
        
        # Fallback to sample data
        logging.info("Using sample satellite data...")
        sample_data = get_offline_tle_data()
        self.satellite_data.parse_tle_data(sample_data)
        logging.info("Loaded sample satellite data")
    
    def get_satellite_positions(self):
        """Get current satellite positions with smooth movement"""
        return self.satellite_data.get_satellite_positions()
    
    def get_satellite_details(self, norad_id):
        """Get detailed satellite information"""
        return self.satellite_data.get_satellite_details(norad_id)
    
    def get_satellite_orbit_path(self, norad_id, duration_hours=3):
        """Get satellite orbit path"""
        return self.satellite_data.get_satellite_orbit_path(norad_id, duration_hours)
    
    def get_future_ground_track(self, norad_id, duration_hours=3):
        """Get satellite ground track"""
        return self.satellite_data.get_future_ground_track(norad_id, duration_hours)
    
    def get_satellite_categories(self):
        """Get satellite categories with counts"""
        return self.categories_manager.get_all_categories()
    
    def search_satellites(self, query):
        """Search satellites by name"""
        query_lower = query.lower()
        results = []
        
        for norad_id, sat_data in self.satellite_data.satellites.items():
            if query_lower in sat_data['name'].lower():
                results.append({
                    'norad_id': norad_id,
                    'name': sat_data['name'],
                    'category': sat_data['category']
                })
        
        return results[:50]  # Limit results
    
    def get_next_passes(self, norad_id, observer_lat, observer_lon, observer_alt=0):
        """Get next satellite passes (simplified)"""
        try:
            from skyfield.api import wgs84
            
            if norad_id not in self.satellite_data.satellites:
                return []
            
            satellite = self.satellite_data.satellites[norad_id]['satellite']
            observer = wgs84.latlon(observer_lat, observer_lon, elevation_m=observer_alt)
            
            current_time = self.satellite_data.ts.now()
            passes = []
            
            # Check visibility over next 24 hours (simplified)
            for hour in range(24):
                t = self.satellite_data.ts.ut1_jd(current_time.ut1 + hour/24)
                try:
                    difference = satellite - observer
                    topocentric = difference.at(t)
                    alt, az, distance = topocentric.altaz()
                    
                    if alt.degrees > 10:  # Visible above 10 degrees
                        passes.append({
                            'time': t.ut1_iso(),
                            'altitude': alt.degrees,
                            'azimuth': az.degrees,
                            'distance': distance.km
                        })
                except:
                    continue
            
            return passes
            
        except Exception as e:
            logging.error(f"Error calculating passes: {e}")
            return []
    
    def refresh_data(self, force=False):
        """Refresh satellite data"""
        if self.offline_mode and not force:
            return False
        
        # Force cache update
        if self.cache_manager.update_tle_cache(force=True):
            self.load_satellite_data()
            return True
        return False
    
    def get_cache_status(self):
        """Get cache status information"""
        return self.cache_manager.get_cache_status()
    
    def get_current_time(self):
        """Get current time in ISO format"""
        return datetime.now().isoformat() + 'Z'
    
    def get_satellite_count(self):
        """Get total number of loaded satellites"""
        return len(self.satellite_data.satellites)