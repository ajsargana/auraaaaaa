
import os
import requests
import json
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

class NASAAsteroidsModule:
    def __init__(self):
        self.api_key = os.environ.get('NASA_API_KEY')
        self.base_url = "https://api.nasa.gov/neo/rest/v1"
        self.cache_dir = "cache"
        self.asteroids_cache_file = os.path.join(self.cache_dir, "nasa_asteroids_cache.json")
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_near_earth_asteroids(self, start_date=None, end_date=None):
        """Get Near Earth Asteroids with daily caching"""
        try:
            # Use today's date if no dates specified
            if not start_date:
                start_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            if not end_date:
                # Get data for 7 days from start date
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = start_dt + timedelta(days=6)  # NeoWs allows max 7 days
                end_date = end_dt.strftime('%Y-%m-%d')
            
            cache_key = f"{start_date}_{end_date}"
            
            # Check cache first
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                logger.info(f"Using cached NASA Asteroids data for {start_date} to {end_date}")
                return cached_data
            
            # If not in cache or cache expired, fetch from API
            if not self.api_key:
                raise ValueError("NASA_API_KEY not found in environment variables")
            
            if self.api_key == "DEMO_KEY":
                logger.warning("Using NASA DEMO_KEY - rate limits apply")
            
            logger.info(f"Fetching NASA Asteroids from API for {start_date} to {end_date}")
            
            # Fetch from NeoWs API
            params = {
                'start_date': start_date,
                'end_date': end_date,
                'api_key': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/feed", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Process the data for frontend consumption
            processed_asteroids = self._process_asteroid_data(data, start_date, end_date)
            
            # Save to cache
            self._save_to_cache(cache_key, processed_asteroids)
            
            return processed_asteroids
            
        except requests.RequestException as e:
            logger.error(f"Error fetching NASA Asteroids: {e}")
            # Check if it's a specific network error
            if "timeout" in str(e).lower():
                error_msg = "Request timed out. NASA API may be temporarily unavailable."
            elif "connection" in str(e).lower():
                error_msg = "Cannot connect to NASA API. Please check your internet connection."
            elif "403" in str(e) or "forbidden" in str(e).lower():
                error_msg = "Access denied by NASA API. API key may be invalid or rate limited."
            elif "404" in str(e):
                error_msg = "NASA API endpoint not found."
            else:
                error_msg = f'Network error: {str(e)}'
            
            return {
                'success': False,
                'error': error_msg,
                'asteroids': [],
                'total_count': 0
            }
        except Exception as e:
            logger.error(f"Unexpected error in NASA Asteroids: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'asteroids': [],
                'total_count': 0
            }
    
    def get_asteroid_details(self, asteroid_id):
        """Get detailed information for a specific asteroid"""
        try:
            logger.info(f"Getting details for asteroid ID: {asteroid_id}")
            
            if not self.api_key:
                logger.error("NASA_API_KEY not found in environment variables")
                raise ValueError("NASA_API_KEY not found in environment variables")
            
            # Validate asteroid_id
            if not asteroid_id or not str(asteroid_id).strip():
                logger.error(f"Invalid asteroid ID: {asteroid_id}")
                return {
                    'success': False,
                    'error': 'Invalid asteroid ID provided'
                }
            
            asteroid_id = str(asteroid_id).strip()
            logger.info(f"Cleaned asteroid ID: {asteroid_id}")
            
            # Check cache first
            cached_details = self._get_asteroid_details_from_cache(asteroid_id)
            if cached_details:
                logger.info(f"Using cached details for asteroid {asteroid_id}")
                return cached_details
            
            logger.info(f"Fetching details from NASA API for asteroid {asteroid_id}")
            
            params = {'api_key': self.api_key}
            api_url = f"{self.base_url}/neo/{asteroid_id}"
            logger.info(f"API URL: {api_url}")
            
            response = requests.get(api_url, params=params, timeout=15)
            logger.info(f"NASA API response status: {response.status_code}")
            
            if response.status_code == 404:
                logger.warning(f"Asteroid {asteroid_id} not found in NASA database")
                return {
                    'success': False,
                    'error': f'Asteroid {asteroid_id} not found in NASA database'
                }
            
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched data for asteroid {asteroid_id}")
            
            # Debug: Log what orbital data NASA provides
            orbital_data = data.get('orbital_data', {})
            logger.info(f"NASA orbital data keys for {asteroid_id}: {list(orbital_data.keys())}")
            if orbital_data:
                logger.info(f"Sample orbital data: orbital_period={orbital_data.get('orbital_period')}, eccentricity={orbital_data.get('eccentricity')}")
            
            # Process asteroid details
            details = self._process_asteroid_details(data)
            
            # Cache the details
            self._cache_asteroid_details(asteroid_id, details)
            
            logger.info(f"Successfully processed details for asteroid {asteroid_id}")
            return details
            
        except requests.RequestException as e:
            logger.error(f"Network error fetching asteroid details {asteroid_id}: {e}")
            return {
                'success': False,
                'error': f'Network error fetching asteroid details: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error fetching asteroid details {asteroid_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to fetch asteroid details: {str(e)}'
            }
    
    def _process_asteroid_data(self, raw_data, start_date, end_date):
        """Process raw API data into frontend-friendly format"""
        try:
            asteroids = []
            total_count = 0
            
            near_earth_objects = raw_data.get('near_earth_objects', {})
            
            for date, daily_asteroids in near_earth_objects.items():
                for asteroid in daily_asteroids:
                    # Get closest approach data
                    closest_approach = None
                    if asteroid.get('close_approach_data'):
                        closest_approach = asteroid['close_approach_data'][0]  # Get the first (closest) approach
                    
                    # Calculate size range
                    estimated_diameter = asteroid.get('estimated_diameter', {})
                    size_km = estimated_diameter.get('kilometers', {})
                    size_range = f"{size_km.get('estimated_diameter_min', 0):.3f} - {size_km.get('estimated_diameter_max', 0):.3f} km"
                    
                    processed_asteroid = {
                        'id': asteroid.get('id', ''),
                        'name': asteroid.get('name', 'Unknown'),
                        'nasa_jpl_url': asteroid.get('nasa_jpl_url', ''),
                        'absolute_magnitude': asteroid.get('absolute_magnitude_h', 0),
                        'estimated_diameter': {
                            'kilometers': size_km,
                            'size_range': size_range
                        },
                        'is_potentially_hazardous': asteroid.get('is_potentially_hazardous_asteroid', False),
                        'close_approach_date': date,
                        'close_approach_data': {
                            'date': closest_approach.get('close_approach_date', '') if closest_approach else '',
                            'velocity_kms': float(closest_approach.get('relative_velocity', {}).get('kilometers_per_second', 0)) if closest_approach else 0,
                            'velocity_kmh': float(closest_approach.get('relative_velocity', {}).get('kilometers_per_hour', 0)) if closest_approach else 0,
                            'miss_distance_km': float(closest_approach.get('miss_distance', {}).get('kilometers', 0)) if closest_approach else 0,
                            'miss_distance_au': float(closest_approach.get('miss_distance', {}).get('astronomical', 0)) if closest_approach else 0,
                            'orbiting_body': closest_approach.get('orbiting_body', 'Earth') if closest_approach else 'Earth'
                        } if closest_approach else None
                    }
                    
                    asteroids.append(processed_asteroid)
                    total_count += 1
            
            # Sort by closest approach date and distance
            asteroids.sort(key=lambda x: (x.get('close_approach_date', ''), x.get('close_approach_data', {}).get('miss_distance_km', float('inf'))))
            
            return {
                'success': True,
                'asteroids': asteroids,
                'total_count': total_count,
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'element_count': raw_data.get('element_count', 0),
                'cached_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing asteroid data: {e}")
            return {
                'success': False,
                'error': f'Error processing data: {str(e)}',
                'asteroids': [],
                'total_count': 0
            }
    
    def _process_asteroid_details(self, raw_data):
        """Process detailed asteroid information"""
        try:
            # Get orbital data
            orbital_data = raw_data.get('orbital_data', {})
            
            # Get all close approaches
            close_approaches = []
            for approach in raw_data.get('close_approach_data', [])[:10]:  # Limit to 10 approaches
                close_approaches.append({
                    'date': approach.get('close_approach_date_full', ''),
                    'velocity_kms': float(approach.get('relative_velocity', {}).get('kilometers_per_second', 0)),
                    'miss_distance_km': float(approach.get('miss_distance', {}).get('kilometers', 0)),
                    'miss_distance_au': float(approach.get('miss_distance', {}).get('astronomical', 0)),
                    'orbiting_body': approach.get('orbiting_body', 'Earth')
                })
            
            # Helper function to safely convert values
            def safe_float(value, default=None):
                if value is None or value == '':
                    return default
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            details = {
                'success': True,
                'id': raw_data.get('id', ''),
                'name': raw_data.get('name', 'Unknown'),
                'nasa_jpl_url': raw_data.get('nasa_jpl_url', ''),
                'absolute_magnitude': safe_float(raw_data.get('absolute_magnitude_h')),
                'estimated_diameter': raw_data.get('estimated_diameter', {}),
                'is_potentially_hazardous': raw_data.get('is_potentially_hazardous_asteroid', False),
                'orbital_data': {
                    'orbit_id': orbital_data.get('orbit_id', ''),
                    'orbit_determination_date': orbital_data.get('orbit_determination_date', ''),
                    'first_observation_date': orbital_data.get('first_observation_date', ''),
                    'last_observation_date': orbital_data.get('last_observation_date', ''),
                    'data_arc_in_days': safe_float(orbital_data.get('data_arc_in_days')),
                    'observations_used': safe_float(orbital_data.get('observations_used')),
                    'orbital_period': safe_float(orbital_data.get('orbital_period')),
                    'minimum_orbit_intersection': safe_float(orbital_data.get('minimum_orbit_intersection')),
                    'jupiter_tisserand_invariant': safe_float(orbital_data.get('jupiter_tisserand_invariant')),
                    'epoch_osculation': orbital_data.get('epoch_osculation', ''),
                    'eccentricity': safe_float(orbital_data.get('eccentricity')),
                    'semi_major_axis': safe_float(orbital_data.get('semi_major_axis')),
                    'inclination': safe_float(orbital_data.get('inclination')),
                    'ascending_node_longitude': safe_float(orbital_data.get('ascending_node_longitude')),
                    'perihelion_distance': safe_float(orbital_data.get('perihelion_distance')),
                    'aphelion_distance': safe_float(orbital_data.get('aphelion_distance'))
                },
                'close_approaches': close_approaches,
                'cached_at': datetime.now(timezone.utc).isoformat()
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error processing asteroid details: {e}")
            return {
                'success': False,
                'error': f'Error processing details: {str(e)}'
            }
    
    def _get_from_cache(self, cache_key):
        """Get asteroid data from cache if available and valid"""
        try:
            if not os.path.exists(self.asteroids_cache_file):
                return None
            
            with open(self.asteroids_cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if we have data for the requested key
            if cache_key not in cache_data:
                return None
            
            cached_item = cache_data[cache_key]
            cached_date = datetime.fromisoformat(cached_item.get('cached_at', ''))
            current_date = datetime.now(timezone.utc)
            
            # Check if cache is from the same day (UTC)
            if cached_date.date() == current_date.date():
                logger.info(f"Found valid cache for {cache_key}")
                return cached_item
            else:
                logger.info(f"Cache for {cache_key} is from a different day, will refresh")
                # Remove expired cache entry
                del cache_data[cache_key]
                self._save_cache_data(cache_data)
                return None
                
        except Exception as e:
            logger.error(f"Error reading asteroids cache: {e}")
            return None
    
    def _save_to_cache(self, cache_key, asteroid_data):
        """Save asteroid data to cache"""
        try:
            # Load existing cache or create new
            cache_data = {}
            if os.path.exists(self.asteroids_cache_file):
                try:
                    with open(self.asteroids_cache_file, 'r') as f:
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
            cache_data[cache_key] = asteroid_data
            
            # Save updated cache
            self._save_cache_data(cache_data)
            logger.info(f"Cached NASA Asteroids data for {cache_key}")
            
        except Exception as e:
            logger.error(f"Error saving asteroids to cache: {e}")
    
    def _get_asteroid_details_from_cache(self, asteroid_id):
        """Get asteroid details from cache"""
        try:
            details_cache_file = os.path.join(self.cache_dir, "nasa_asteroid_details_cache.json")
            
            if not os.path.exists(details_cache_file):
                return None
            
            with open(details_cache_file, 'r') as f:
                cache_data = json.load(f)
            
            if asteroid_id not in cache_data:
                return None
            
            cached_item = cache_data[asteroid_id]
            cached_date = datetime.fromisoformat(cached_item.get('cached_at', ''))
            current_date = datetime.now(timezone.utc)
            
            # Cache details for 24 hours
            if (current_date - cached_date).total_seconds() < 86400:
                return cached_item
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading asteroid details cache: {e}")
            return None
    
    def _cache_asteroid_details(self, asteroid_id, details):
        """Cache asteroid details"""
        try:
            details_cache_file = os.path.join(self.cache_dir, "nasa_asteroid_details_cache.json")
            
            cache_data = {}
            if os.path.exists(details_cache_file):
                try:
                    with open(details_cache_file, 'r') as f:
                        cache_data = json.load(f)
                except:
                    pass
            
            cache_data[asteroid_id] = details
            
            with open(details_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error caching asteroid details: {e}")
    
    def _save_cache_data(self, cache_data):
        """Save cache data to file"""
        try:
            with open(self.asteroids_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing asteroids cache file: {e}")
    
    def clear_cache(self):
        """Clear all cached asteroid data"""
        try:
            if os.path.exists(self.asteroids_cache_file):
                os.remove(self.asteroids_cache_file)
            
            details_cache_file = os.path.join(self.cache_dir, "nasa_asteroid_details_cache.json")
            if os.path.exists(details_cache_file):
                os.remove(details_cache_file)
            
            logger.info("NASA Asteroids cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing asteroids cache: {e}")
        return False
    
    def get_cache_info(self):
        """Get information about cached data"""
        try:
            info = {
                'main_cache': {'cached_keys': [], 'cache_size': 0},
                'details_cache': {'cached_ids': [], 'cache_size': 0}
            }
            
            # Main cache info
            if os.path.exists(self.asteroids_cache_file):
                with open(self.asteroids_cache_file, 'r') as f:
                    cache_data = json.load(f)
                info['main_cache'] = {
                    'cached_keys': list(cache_data.keys()),
                    'cache_size': len(cache_data),
                    'cache_file_size': os.path.getsize(self.asteroids_cache_file)
                }
            
            # Details cache info
            details_cache_file = os.path.join(self.cache_dir, "nasa_asteroid_details_cache.json")
            if os.path.exists(details_cache_file):
                with open(details_cache_file, 'r') as f:
                    details_cache = json.load(f)
                info['details_cache'] = {
                    'cached_ids': list(details_cache.keys()),
                    'cache_size': len(details_cache),
                    'cache_file_size': os.path.getsize(details_cache_file)
                }
            
            return info
        except Exception as e:
            logger.error(f"Error getting asteroids cache info: {e}")
            return {'main_cache': {'cached_keys': [], 'cache_size': 0}, 'details_cache': {'cached_ids': [], 'cache_size': 0}}
    
    def get_asteroid_stats(self):
        """Get statistics about currently tracked asteroids"""
        try:
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            end_date = (datetime.now(timezone.utc) + timedelta(days=6)).strftime('%Y-%m-%d')
            
            asteroids_data = self.get_near_earth_asteroids(today, end_date)
            
            if not asteroids_data['success']:
                return asteroids_data
            
            asteroids = asteroids_data['asteroids']
            
            # Calculate statistics
            total_count = len(asteroids)
            hazardous_count = sum(1 for a in asteroids if a['is_potentially_hazardous'])
            
            # Size categories
            large_asteroids = 0
            medium_asteroids = 0
            small_asteroids = 0
            
            # Speed categories
            fast_asteroids = 0
            
            for asteroid in asteroids:
                # Size classification (using max diameter in km)
                max_size = asteroid.get('estimated_diameter', {}).get('kilometers', {}).get('estimated_diameter_max', 0)
                if max_size > 1.0:
                    large_asteroids += 1
                elif max_size > 0.14:
                    medium_asteroids += 1
                else:
                    small_asteroids += 1
                
                # Speed classification (> 20 km/s is considered fast)
                velocity = asteroid.get('close_approach_data', {}).get('velocity_kms', 0) if asteroid.get('close_approach_data') else 0
                if velocity > 20:
                    fast_asteroids += 1
            
            return {
                'success': True,
                'stats': {
                    'total_count': total_count,
                    'potentially_hazardous': hazardous_count,
                    'non_hazardous': total_count - hazardous_count,
                    'size_categories': {
                        'large': large_asteroids,
                        'medium': medium_asteroids,
                        'small': small_asteroids
                    },
                    'fast_moving': fast_asteroids,
                    'date_range': asteroids_data['date_range']
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting asteroid stats: {e}")
            return {
                'success': False,
                'error': str(e)
            }
