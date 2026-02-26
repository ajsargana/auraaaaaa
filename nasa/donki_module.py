
import os
import requests
import json
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

class DONKIModule:
    def __init__(self):
        self.api_key = os.environ.get('NASA_API_KEY')
        self.base_url = "https://api.nasa.gov/DONKI"
        self.cache_dir = "cache"
        self.donki_cache_file = os.path.join(self.cache_dir, "nasa_donki_cache.json")
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_space_weather_data(self):
        """Get NASA DONKI space weather data with daily caching"""
        try:
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            
            # Check cache first
            cached_data = self._get_from_cache(today)
            if cached_data:
                logger.info(f"Using cached NASA DONKI data for {today}")
                return cached_data
            
            if not self.api_key:
                raise ValueError("NASA_API_KEY not found in environment variables")
            
            logger.info(f"Fetching NASA DONKI data from API for {today}")
            
            # Get date range - last 30 days to today
            start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = today
            
            # Fetch different types of space weather events
            space_weather_data = {
                'solar_flares': self._fetch_solar_flares(start_date, end_date),
                'coronal_mass_ejections': self._fetch_cme(start_date, end_date),
                'geomagnetic_storms': self._fetch_geomagnetic_storms(start_date, end_date),
                'solar_energetic_particles': self._fetch_sep(start_date, end_date),
                'magnetopause_crossings': self._fetch_mpc(start_date, end_date),
                'radiation_belt_enhancements': self._fetch_rbe(start_date, end_date),
                'high_speed_streams': self._fetch_hss(start_date, end_date)
            }
            
            # Process and combine all data
            processed_data = self._process_space_weather_data(space_weather_data, today)
            
            # Save to cache
            self._save_to_cache(today, processed_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error fetching NASA DONKI data: {e}")
            return {
                'success': False,
                'error': f'Failed to fetch space weather data: {str(e)}',
                'space_weather': {}
            }
    
    def _fetch_solar_flares(self, start_date, end_date):
        """Fetch solar flare data from DONKI"""
        try:
            params = {
                'startDate': start_date,
                'endDate': end_date,
                'api_key': self.api_key
            }
            response = requests.get(f"{self.base_url}/FLR", params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching solar flares: {e}")
            return []
    
    def _fetch_cme(self, start_date, end_date):
        """Fetch Coronal Mass Ejection data from DONKI"""
        try:
            params = {
                'startDate': start_date,
                'endDate': end_date,
                'api_key': self.api_key
            }
            response = requests.get(f"{self.base_url}/CME", params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching CME data: {e}")
            return []
    
    def _fetch_geomagnetic_storms(self, start_date, end_date):
        """Fetch Geomagnetic Storm data from DONKI"""
        try:
            params = {
                'startDate': start_date,
                'endDate': end_date,
                'api_key': self.api_key
            }
            response = requests.get(f"{self.base_url}/GST", params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching geomagnetic storms: {e}")
            return []
    
    def _fetch_sep(self, start_date, end_date):
        """Fetch Solar Energetic Particle data from DONKI"""
        try:
            params = {
                'startDate': start_date,
                'endDate': end_date,
                'api_key': self.api_key
            }
            response = requests.get(f"{self.base_url}/SEP", params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching SEP data: {e}")
            return []
    
    def _fetch_mpc(self, start_date, end_date):
        """Fetch Magnetopause Crossing data from DONKI"""
        try:
            params = {
                'startDate': start_date,
                'endDate': end_date,
                'api_key': self.api_key
            }
            response = requests.get(f"{self.base_url}/MPC", params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching MPC data: {e}")
            return []
    
    def _fetch_rbe(self, start_date, end_date):
        """Fetch Radiation Belt Enhancement data from DONKI"""
        try:
            params = {
                'startDate': start_date,
                'endDate': end_date,
                'api_key': self.api_key
            }
            response = requests.get(f"{self.base_url}/RBE", params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching RBE data: {e}")
            return []
    
    def _fetch_hss(self, start_date, end_date):
        """Fetch High Speed Stream data from DONKI"""
        try:
            params = {
                'startDate': start_date,
                'endDate': end_date,
                'api_key': self.api_key
            }
            response = requests.get(f"{self.base_url}/HSS", params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching HSS data: {e}")
            return []
    
    def _process_space_weather_data(self, raw_data, date):
        """Process raw space weather data into frontend-friendly format"""
        try:
            processed = {
                'success': True,
                'date': date,
                'space_weather': {
                    'solar_flares': {
                        'count': len(raw_data.get('solar_flares', [])),
                        'events': self._process_solar_flares(raw_data.get('solar_flares', []))
                    },
                    'coronal_mass_ejections': {
                        'count': len(raw_data.get('coronal_mass_ejections', [])),
                        'events': self._process_cme(raw_data.get('coronal_mass_ejections', []))
                    },
                    'geomagnetic_storms': {
                        'count': len(raw_data.get('geomagnetic_storms', [])),
                        'events': self._process_geomagnetic_storms(raw_data.get('geomagnetic_storms', []))
                    },
                    'solar_energetic_particles': {
                        'count': len(raw_data.get('solar_energetic_particles', [])),
                        'events': self._process_sep(raw_data.get('solar_energetic_particles', []))
                    },
                    'magnetopause_crossings': {
                        'count': len(raw_data.get('magnetopause_crossings', [])),
                        'events': self._process_mpc(raw_data.get('magnetopause_crossings', []))
                    },
                    'radiation_belt_enhancements': {
                        'count': len(raw_data.get('radiation_belt_enhancements', [])),
                        'events': self._process_rbe(raw_data.get('radiation_belt_enhancements', []))
                    },
                    'high_speed_streams': {
                        'count': len(raw_data.get('high_speed_streams', [])),
                        'events': self._process_hss(raw_data.get('high_speed_streams', []))
                    }
                },
                'summary': self._generate_summary(raw_data),
                'cached_at': datetime.now(timezone.utc).isoformat()
            }
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing space weather data: {e}")
            return {
                'success': False,
                'error': f'Error processing data: {str(e)}',
                'space_weather': {}
            }
    
    def _process_solar_flares(self, flares):
        """Process solar flare events"""
        processed = []
        for flare in flares[:20]:  # Limit to 20 most recent
            processed.append({
                'flare_id': flare.get('flrID', ''),
                'begin_time': flare.get('beginTime', ''),
                'peak_time': flare.get('peakTime', ''),
                'end_time': flare.get('endTime', ''),
                'class_type': flare.get('classType', 'Unknown'),
                'source_location': flare.get('sourceLocation', ''),
                'active_region_num': flare.get('activeRegionNum', ''),
                'link': flare.get('link', '')
            })
        return processed
    
    def _process_cme(self, cmes):
        """Process Coronal Mass Ejection events"""
        processed = []
        for cme in cmes[:20]:  # Limit to 20 most recent
            processed.append({
                'activity_id': cme.get('activityID', ''),
                'start_time': cme.get('startTime', ''),
                'source_location': cme.get('sourceLocation', ''),
                'note': cme.get('note', ''),
                'link': cme.get('link', ''),
                'instruments': [inst.get('displayName', '') for inst in cme.get('instruments', [])]
            })
        return processed
    
    def _process_geomagnetic_storms(self, storms):
        """Process Geomagnetic Storm events"""
        processed = []
        for storm in storms[:20]:  # Limit to 20 most recent
            processed.append({
                'gst_id': storm.get('gstID', ''),
                'start_time': storm.get('startTime', ''),
                'all_kp_index': storm.get('allKpIndex', []),
                'link': storm.get('link', '')
            })
        return processed
    
    def _process_sep(self, seps):
        """Process Solar Energetic Particle events"""
        processed = []
        for sep in seps[:20]:  # Limit to 20 most recent
            processed.append({
                'sep_id': sep.get('sepID', ''),
                'event_time': sep.get('eventTime', ''),
                'instruments': [inst.get('displayName', '') for inst in sep.get('instruments', [])],
                'link': sep.get('link', '')
            })
        return processed
    
    def _process_mpc(self, mpcs):
        """Process Magnetopause Crossing events"""
        processed = []
        for mpc in mpcs[:20]:  # Limit to 20 most recent
            processed.append({
                'event_time': mpc.get('eventTime', ''),
                'instruments': [inst.get('displayName', '') for inst in mpc.get('instruments', [])],
                'link': mpc.get('link', '')
            })
        return processed
    
    def _process_rbe(self, rbes):
        """Process Radiation Belt Enhancement events"""
        processed = []
        for rbe in rbes[:20]:  # Limit to 20 most recent
            processed.append({
                'rbe_id': rbe.get('rbeID', ''),
                'event_time': rbe.get('eventTime', ''),
                'instruments': [inst.get('displayName', '') for inst in rbe.get('instruments', [])],
                'link': rbe.get('link', '')
            })
        return processed
    
    def _process_hss(self, hsses):
        """Process High Speed Stream events"""
        processed = []
        for hss in hsses[:20]:  # Limit to 20 most recent
            processed.append({
                'hss_id': hss.get('hssID', ''),
                'event_time': hss.get('eventTime', ''),
                'instruments': [inst.get('displayName', '') for inst in hss.get('instruments', [])],
                'link': hss.get('link', '')
            })
        return processed
    
    def _generate_summary(self, raw_data):
        """Generate summary statistics"""
        total_events = sum([
            len(raw_data.get('solar_flares', [])),
            len(raw_data.get('coronal_mass_ejections', [])),
            len(raw_data.get('geomagnetic_storms', [])),
            len(raw_data.get('solar_energetic_particles', [])),
            len(raw_data.get('magnetopause_crossings', [])),
            len(raw_data.get('radiation_belt_enhancements', [])),
            len(raw_data.get('high_speed_streams', []))
        ])
        
        return {
            'total_events': total_events,
            'most_active_category': self._find_most_active_category(raw_data),
            'recent_activity_level': 'High' if total_events > 50 else 'Moderate' if total_events > 20 else 'Low'
        }
    
    def _find_most_active_category(self, raw_data):
        """Find the category with most events"""
        categories = {
            'Solar Flares': len(raw_data.get('solar_flares', [])),
            'Coronal Mass Ejections': len(raw_data.get('coronal_mass_ejections', [])),
            'Geomagnetic Storms': len(raw_data.get('geomagnetic_storms', [])),
            'Solar Energetic Particles': len(raw_data.get('solar_energetic_particles', [])),
            'Magnetopause Crossings': len(raw_data.get('magnetopause_crossings', [])),
            'Radiation Belt Enhancements': len(raw_data.get('radiation_belt_enhancements', [])),
            'High Speed Streams': len(raw_data.get('high_speed_streams', []))
        }
        
        return max(categories, key=categories.get) if any(categories.values()) else 'None'
    
    def _get_from_cache(self, date):
        """Get DONKI data from cache if available and valid"""
        try:
            if not os.path.exists(self.donki_cache_file):
                return None
            
            with open(self.donki_cache_file, 'r') as f:
                cache_data = json.load(f)
            
            if date not in cache_data:
                return None
            
            cached_item = cache_data[date]
            cached_datetime = datetime.fromisoformat(cached_item.get('cached_at', ''))
            current_datetime = datetime.now(timezone.utc)
            
            # Check if cache is from the same day (UTC)
            if cached_datetime.date() == current_datetime.date():
                logger.info(f"Found valid cache for {date}")
                return cached_item
            else:
                logger.info(f"Cache for {date} is from a different day, will refresh")
                # Remove expired cache entry
                del cache_data[date]
                self._save_cache_data(cache_data)
                return None
                
        except Exception as e:
            logger.error(f"Error reading DONKI cache: {e}")
            return None
    
    def _save_to_cache(self, date, donki_data):
        """Save DONKI data to cache"""
        try:
            # Load existing cache or create new
            cache_data = {}
            if os.path.exists(self.donki_cache_file):
                try:
                    with open(self.donki_cache_file, 'r') as f:
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
            cache_data[date] = donki_data
            
            # Save updated cache
            self._save_cache_data(cache_data)
            logger.info(f"Cached NASA DONKI data for {date}")
            
        except Exception as e:
            logger.error(f"Error saving DONKI to cache: {e}")
    
    def _save_cache_data(self, cache_data):
        """Save cache data to file"""
        try:
            with open(self.donki_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing DONKI cache file: {e}")
    
    def clear_cache(self):
        """Clear all cached DONKI data"""
        try:
            if os.path.exists(self.donki_cache_file):
                os.remove(self.donki_cache_file)
                logger.info("NASA DONKI cache cleared")
                return True
        except Exception as e:
            logger.error(f"Error clearing DONKI cache: {e}")
        return False
    
    def get_cache_info(self):
        """Get information about cached data"""
        try:
            if not os.path.exists(self.donki_cache_file):
                return {'cached_dates': [], 'cache_size': 0}
            
            with open(self.donki_cache_file, 'r') as f:
                cache_data = json.load(f)
            
            return {
                'cached_dates': list(cache_data.keys()),
                'cache_size': len(cache_data),
                'cache_file_size': os.path.getsize(self.donki_cache_file)
            }
        except Exception as e:
            logger.error(f"Error getting DONKI cache info: {e}")
            return {'cached_dates': [], 'cache_size': 0}
