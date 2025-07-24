import os
import json
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path

class CacheManager:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.tle_cache_file = self.cache_dir / "tle_data.txt"
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.update_interval_days = 7  # Update TLE data weekly
        
    def get_metadata(self):
        """Get cache metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'last_update': None,
            'satellite_count': 0,
            'sources_loaded': 0
        }
    
    def save_metadata(self, metadata):
        """Save cache metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save metadata: {e}")
    
    def needs_update(self):
        """Check if cache needs updating"""
        metadata = self.get_metadata()
        if not metadata.get('last_update'):
            return True
        
        last_update = datetime.fromisoformat(metadata['last_update'])
        return datetime.now() - last_update > timedelta(days=self.update_interval_days)
    
    def has_cached_data(self):
        """Check if cached TLE data exists"""
        return self.tle_cache_file.exists() and self.tle_cache_file.stat().st_size > 0
    
    def get_cached_tle_data(self):
        """Load TLE data from cache"""
        try:
            if self.has_cached_data():
                with open(self.tle_cache_file, 'r') as f:
                    return f.read()
        except Exception as e:
            logging.error(f"Failed to read cached TLE data: {e}")
        return None
    
    def update_tle_cache(self, force=False):
        """Update TLE cache from online sources"""
        if not force and not self.needs_update():
            logging.info("TLE cache is up to date")
            return True
        
        logging.info("Updating TLE cache from online sources...")
        
        tle_sources = [
            "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
            "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
            "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle",
            "https://celestrak.org/NORAD/elements/gp.php?GROUP=noaa&FORMAT=tle",
            "https://celestrak.org/NORAD/elements/gp.php?GROUP=goes&FORMAT=tle",
            "https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle"
        ]
        
        all_tle_data = []
        sources_loaded = 0
        
        for source_url in tle_sources:
            try:
                response = requests.get(source_url, timeout=30)
                response.raise_for_status()
                all_tle_data.append(response.text)
                sources_loaded += 1
                logging.info(f"Loaded TLE data from {source_url}")
            except Exception as e:
                logging.warning(f"Failed to load from {source_url}: {e}")
        
        if all_tle_data:
            combined_data = "\n".join(all_tle_data)
            
            # Save to cache
            try:
                with open(self.tle_cache_file, 'w') as f:
                    f.write(combined_data)
                
                # Update metadata
                metadata = {
                    'last_update': datetime.now().isoformat(),
                    'satellite_count': self._count_satellites(combined_data),
                    'sources_loaded': sources_loaded,
                    'data_size': len(combined_data)
                }
                self.save_metadata(metadata)
                
                logging.info(f"TLE cache updated successfully: {metadata['satellite_count']} satellites")
                return True
                
            except Exception as e:
                logging.error(f"Failed to save TLE cache: {e}")
        
        return False
    
    def _count_satellites(self, tle_data):
        """Count satellites in TLE data"""
        lines = tle_data.strip().split('\n')
        return len(lines) // 3  # 3 lines per satellite
    
    def get_cache_status(self):
        """Get cache status information"""
        metadata = self.get_metadata()
        return {
            'has_cache': self.has_cached_data(),
            'needs_update': self.needs_update(),
            'last_update': metadata.get('last_update'),
            'satellite_count': metadata.get('satellite_count', 0),
            'sources_loaded': metadata.get('sources_loaded', 0),
            'cache_age_days': self._get_cache_age_days(),
            'next_update_due': self._get_next_update_date()
        }
    
    def _get_cache_age_days(self):
        """Get cache age in days"""
        metadata = self.get_metadata()
        if metadata.get('last_update'):
            last_update = datetime.fromisoformat(metadata['last_update'])
            return (datetime.now() - last_update).days
        return None
    
    def _get_next_update_date(self):
        """Get next scheduled update date"""
        metadata = self.get_metadata()
        if metadata.get('last_update'):
            last_update = datetime.fromisoformat(metadata['last_update'])
            next_update = last_update + timedelta(days=self.update_interval_days)
            return next_update.isoformat()
        return None