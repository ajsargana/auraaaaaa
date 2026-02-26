
import os
import requests
import json
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class NASAAPODModule:
    def __init__(self):
        self.api_key = os.environ.get('NASA_API_KEY')
        self.base_url = "https://api.nasa.gov/planetary/apod"
        self.cache_dir = "cache"
        self.apod_cache_file = os.path.join(self.cache_dir, "nasa_apod_cache.json")
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
    def get_picture_of_the_day(self, date=None):
        """Get NASA's Astronomy Picture of the Day with daily caching"""
        try:
            # Use today's date if no date specified
            request_date = date or datetime.now(timezone.utc).strftime('%Y-%m-%d')
            
            # Check cache first
            cached_data = self._get_from_cache(request_date)
            if cached_data:
                logger.info(f"Using cached NASA APOD data for {request_date}")
                return cached_data
            
            # If not in cache or cache expired, fetch from API
            if not self.api_key:
                raise ValueError("NASA_API_KEY not found in environment variables")
            
            logger.info(f"Fetching NASA APOD from API for {request_date}")
            
            params = {
                'api_key': self.api_key,
                'thumbs': True
            }
            
            if date:
                params['date'] = date
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Process the data for frontend consumption
            apod_data = {
                'success': True,
                'title': data.get('title', 'NASA Picture of the Day'),
                'explanation': data.get('explanation', ''),
                'date': data.get('date', request_date),
                'media_type': data.get('media_type', 'image'),
                'url': data.get('url', ''),
                'hdurl': data.get('hdurl', data.get('url', '')),  # High-definition URL
                'thumbnail_url': data.get('thumbnail_url', ''),
                'copyright': data.get('copyright', ''),
                'service_version': data.get('service_version', 'v1'),
                'cached_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Save to cache
            self._save_to_cache(request_date, apod_data)
            
            return apod_data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching NASA APOD: {e}")
            return {
                'success': False,
                'error': f'Failed to fetch NASA Picture of the Day: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error in NASA APOD: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def _get_from_cache(self, date):
        """Get APOD data from cache if available and valid"""
        try:
            if not os.path.exists(self.apod_cache_file):
                return None
            
            with open(self.apod_cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if we have data for the requested date
            if date not in cache_data:
                return None
            
            cached_item = cache_data[date]
            cached_date = datetime.fromisoformat(cached_item.get('cached_at', ''))
            current_date = datetime.now(timezone.utc)
            
            # Check if cache is from the same day (UTC)
            if cached_date.date() == current_date.date():
                logger.info(f"Found valid cache for {date}")
                return cached_item
            else:
                logger.info(f"Cache for {date} is from a different day, will refresh")
                # Remove expired cache entry
                del cache_data[date]
                self._save_cache_data(cache_data)
                return None
                
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None
    
    def _save_to_cache(self, date, apod_data):
        """Save APOD data to cache"""
        try:
            # Load existing cache or create new
            cache_data = {}
            if os.path.exists(self.apod_cache_file):
                try:
                    with open(self.apod_cache_file, 'r') as f:
                        cache_data = json.load(f)
                except:
                    pass  # Start with empty cache if file is corrupted
            
            # Clean old entries (keep only today's entries)
            current_date = datetime.now(timezone.utc).date()
            cache_data = {
                k: v for k, v in cache_data.items() 
                if datetime.fromisoformat(v.get('cached_at', '')).date() == current_date
            }
            
            # Add new entry
            cache_data[date] = apod_data
            
            # Save updated cache
            self._save_cache_data(cache_data)
            logger.info(f"Cached NASA APOD data for {date}")
            
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
    
    def _save_cache_data(self, cache_data):
        """Save cache data to file"""
        try:
            with open(self.apod_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing cache file: {e}")
    
    def clear_cache(self):
        """Clear all cached APOD data"""
        try:
            if os.path.exists(self.apod_cache_file):
                os.remove(self.apod_cache_file)
                logger.info("NASA APOD cache cleared")
                return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
        return False
    
    def get_cache_info(self):
        """Get information about cached data"""
        try:
            if not os.path.exists(self.apod_cache_file):
                return {'cached_dates': [], 'cache_size': 0}
            
            with open(self.apod_cache_file, 'r') as f:
                cache_data = json.load(f)
            
            return {
                'cached_dates': list(cache_data.keys()),
                'cache_size': len(cache_data),
                'cache_file_size': os.path.getsize(self.apod_cache_file)
            }
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {'cached_dates': [], 'cache_size': 0}

    def get_recent_pictures(self, count=5):
        """Get recent pictures from NASA APOD"""
        try:
            if not self.api_key:
                raise ValueError("NASA_API_KEY not found in environment variables")
            
            params = {
                'api_key': self.api_key,
                'count': min(count, 10),  # Limit to 10 max
                'thumbs': True
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Process multiple pictures
            pictures = []
            for item in data:
                pictures.append({
                    'title': item.get('title', 'NASA Picture'),
                    'explanation': item.get('explanation', ''),
                    'date': item.get('date', ''),
                    'media_type': item.get('media_type', 'image'),
                    'url': item.get('url', ''),
                    'hdurl': item.get('hdurl', item.get('url', '')),
                    'thumbnail_url': item.get('thumbnail_url', ''),
                    'copyright': item.get('copyright', '')
                })
            
            return {
                'success': True,
                'pictures': pictures,
                'count': len(pictures)
            }
            
        except Exception as e:
            logger.error(f"Error fetching recent NASA APODs: {e}")
            return {
                'success': False,
                'error': f'Failed to fetch recent pictures: {str(e)}',
                'pictures': [],
                'count': 0
            }
