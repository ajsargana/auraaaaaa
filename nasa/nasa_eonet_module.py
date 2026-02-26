
import os
import requests
import json
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class NASAEONETModule:
    def __init__(self):
        self.api_key = os.environ.get('NASA_API_KEY')
        self.base_url = "https://eonet.gsfc.nasa.gov/api/v3"
        self.cache_dir = "cache"
        self.eonet_cache_file = os.path.join(self.cache_dir, "nasa_eonet_cache.json")
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_natural_events(self):
        """Get NASA EONET natural events with daily caching"""
        try:
            # Check cache first
            cached_data = self._get_from_cache()
            if cached_data:
                logger.info("Using cached NASA EONET data")
                return cached_data
            
            logger.info("Fetching NASA EONET data from API")
            
            # Fetch events data
            events_response = requests.get(f"{self.base_url}/events", timeout=30)
            events_response.raise_for_status()
            events_data = events_response.json()
            
            # Fetch categories data
            categories_response = requests.get(f"{self.base_url}/categories", timeout=30)
            categories_response.raise_for_status()
            categories_data = categories_response.json()
            
            # Process the data for frontend consumption
            processed_data = self._process_eonet_data(events_data, categories_data)
            
            # Save to cache
            self._save_to_cache(processed_data)
            
            return processed_data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching NASA EONET data: {e}")
            # Check if it's a specific network error
            if "timeout" in str(e).lower():
                error_msg = "Request timed out. NASA EONET API may be temporarily unavailable."
            elif "connection" in str(e).lower():
                error_msg = "Cannot connect to NASA EONET API. Please check your internet connection."
            elif "404" in str(e):
                error_msg = "NASA EONET API endpoint not found."
            else:
                error_msg = f'Network error: {str(e)}'
            
            return {
                'success': False,
                'error': error_msg,
                'events': [],
                'categories': {},
                'total_count': 0
            }
        except Exception as e:
            logger.error(f"Unexpected error in NASA EONET: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'events': [],
                'categories': {},
                'total_count': 0
            }
    
    def get_event_details(self, event_id):
        """Get detailed information for a specific event"""
        try:
            logger.info(f"Getting details for event ID: {event_id}")
            
            # Check cache first for event details
            cached_details = self._get_event_details_from_cache(event_id)
            if cached_details:
                logger.info(f"Using cached details for event {event_id}")
                return cached_details
            
            logger.info(f"Fetching details from NASA EONET API for event {event_id}")
            
            response = requests.get(f"{self.base_url}/events/{event_id}", timeout=15)
            
            if response.status_code == 404:
                logger.warning(f"Event {event_id} not found in NASA EONET database")
                return {
                    'success': False,
                    'error': f'Event {event_id} not found in NASA EONET database'
                }
            
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched data for event {event_id}")
            
            # Process event details
            details = self._process_event_details(data)
            
            # Cache the details
            self._cache_event_details(event_id, details)
            
            logger.info(f"Successfully processed details for event {event_id}")
            return details
            
        except requests.RequestException as e:
            logger.error(f"Network error fetching event details {event_id}: {e}")
            return {
                'success': False,
                'error': f'Network error fetching event details: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error fetching event details {event_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to fetch event details: {str(e)}'
            }
    
    def _process_eonet_data(self, events_data, categories_data):
        """Process raw API data into frontend-friendly format"""
        try:
            events = []
            categories = {}
            
            # Process categories
            for category in categories_data.get('categories', []):
                categories[category['id']] = {
                    'title': category['title'],
                    'description': category.get('description', ''),
                    'link': category.get('link', '')
                }
            
            # Process events
            for event in events_data.get('events', []):
                # Get the most recent geometry for location
                latest_geometry = None
                if event.get('geometry') and len(event['geometry']) > 0:
                    latest_geometry = event['geometry'][-1]  # Most recent geometry
                
                processed_event = {
                    'id': event.get('id', ''),
                    'title': event.get('title', 'Unknown Event'),
                    'description': event.get('description', ''),
                    'link': event.get('link', ''),
                    'closed': event.get('closed', None),
                    'category_id': event.get('categories', [{}])[0].get('id', '') if event.get('categories') else '',
                    'category_title': event.get('categories', [{}])[0].get('title', 'Unknown') if event.get('categories') else 'Unknown',
                    'location': {
                        'type': latest_geometry.get('type', '') if latest_geometry else '',
                        'coordinates': latest_geometry.get('coordinates', []) if latest_geometry else [],
                        'date': latest_geometry.get('date', '') if latest_geometry else ''
                    } if latest_geometry else None,
                    'sources': [
                        {
                            'id': source.get('id', ''),
                            'url': source.get('url', '')
                        }
                        for source in event.get('sources', [])
                    ]
                }
                
                events.append(processed_event)
            
            # Sort events by most recent first
            events.sort(key=lambda x: x.get('location', {}).get('date', ''), reverse=True)
            
            return {
                'success': True,
                'events': events,
                'categories': categories,
                'total_count': len(events),
                'cached_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing EONET data: {e}")
            return {
                'success': False,
                'error': f'Error processing data: {str(e)}',
                'events': [],
                'categories': {},
                'total_count': 0
            }
    
    def _process_event_details(self, raw_data):
        """Process detailed event information"""
        try:
            event = raw_data
            
            # Process all geometries (event evolution over time)
            geometries = []
            for geom in event.get('geometry', []):
                geometries.append({
                    'date': geom.get('date', ''),
                    'type': geom.get('type', ''),
                    'coordinates': geom.get('coordinates', [])
                })
            
            details = {
                'success': True,
                'id': event.get('id', ''),
                'title': event.get('title', 'Unknown Event'),
                'description': event.get('description', ''),
                'link': event.get('link', ''),
                'closed': event.get('closed', None),
                'categories': [
                    {
                        'id': cat.get('id', ''),
                        'title': cat.get('title', ''),
                        'link': cat.get('link', '')
                    }
                    for cat in event.get('categories', [])
                ],
                'sources': [
                    {
                        'id': source.get('id', ''),
                        'url': source.get('url', '')
                    }
                    for source in event.get('sources', [])
                ],
                'geometries': geometries,
                'cached_at': datetime.now(timezone.utc).isoformat()
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error processing event details: {e}")
            return {
                'success': False,
                'error': f'Error processing details: {str(e)}'
            }
    
    def _get_from_cache(self):
        """Get EONET data from cache if available and valid"""
        try:
            if not os.path.exists(self.eonet_cache_file):
                return None
            
            # Read cache file with minimal processing
            with open(self.eonet_cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if we have main data
            if 'main_data' not in cache_data:
                return None
            
            cached_item = cache_data['main_data']
            
            # Fast cache validation - just check if cached_at exists and is recent
            if 'cached_at' not in cached_item:
                return None
                
            try:
                cached_date = datetime.fromisoformat(cached_item['cached_at'])
                current_date = datetime.now(timezone.utc)
                
                # Check if cache is from the same day (UTC)
                if cached_date.date() == current_date.date():
                    logger.info(f"Found valid EONET cache with {len(cached_item.get('events', []))} events")
                    return cached_item
                else:
                    logger.info("EONET cache is from a different day, will refresh")
                    return None
            except (ValueError, TypeError):
                logger.warning("Invalid cache timestamp format")
                return None
                
        except Exception as e:
            logger.error(f"Error reading EONET cache: {e}")
            return None
    
    def _save_to_cache(self, eonet_data):
        """Save EONET data to cache"""
        try:
            # Load existing cache or create new
            cache_data = {}
            if os.path.exists(self.eonet_cache_file):
                try:
                    with open(self.eonet_cache_file, 'r') as f:
                        cache_data = json.load(f)
                except:
                    pass  # Start with empty cache if file is corrupted
            
            # Clean old entries (keep only today's entries)
            current_date = datetime.now(timezone.utc).date()
            
            # Clean main data if from different day
            if 'main_data' in cache_data:
                try:
                    cached_date = datetime.fromisoformat(cache_data['main_data'].get('cached_at', ''))
                    if cached_date.date() != current_date:
                        del cache_data['main_data']
                except:
                    del cache_data['main_data']
            
            # Clean event details if from different day
            if 'event_details' in cache_data:
                cache_data['event_details'] = {
                    k: v for k, v in cache_data['event_details'].items()
                    if datetime.fromisoformat(v.get('cached_at', '')).date() == current_date
                }
            
            # Add new main data entry
            cache_data['main_data'] = eonet_data
            
            # Save updated cache
            self._save_cache_data(cache_data)
            logger.info("Cached NASA EONET data")
            
        except Exception as e:
            logger.error(f"Error saving EONET data to cache: {e}")
    
    def _get_event_details_from_cache(self, event_id):
        """Get event details from cache"""
        try:
            if not os.path.exists(self.eonet_cache_file):
                return None
            
            with open(self.eonet_cache_file, 'r') as f:
                cache_data = json.load(f)
            
            if 'event_details' not in cache_data or event_id not in cache_data['event_details']:
                return None
            
            cached_item = cache_data['event_details'][event_id]
            cached_date = datetime.fromisoformat(cached_item.get('cached_at', ''))
            current_date = datetime.now(timezone.utc)
            
            # Cache details for the same day
            if cached_date.date() == current_date.date():
                return cached_item
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading event details cache: {e}")
            return None
    
    def _cache_event_details(self, event_id, details):
        """Cache event details"""
        try:
            cache_data = {}
            if os.path.exists(self.eonet_cache_file):
                try:
                    with open(self.eonet_cache_file, 'r') as f:
                        cache_data = json.load(f)
                except:
                    pass
            
            if 'event_details' not in cache_data:
                cache_data['event_details'] = {}
            
            cache_data['event_details'][event_id] = details
            
            self._save_cache_data(cache_data)
                
        except Exception as e:
            logger.error(f"Error caching event details: {e}")
    
    def _save_cache_data(self, cache_data):
        """Save cache data to file"""
        try:
            with open(self.eonet_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing EONET cache file: {e}")
    
    def clear_cache(self):
        """Clear all cached EONET data"""
        try:
            if os.path.exists(self.eonet_cache_file):
                os.remove(self.eonet_cache_file)
            
            logger.info("NASA EONET cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing EONET cache: {e}")
        return False
    
    def get_cache_info(self):
        """Get information about cached data"""
        try:
            if not os.path.exists(self.eonet_cache_file):
                return {
                    'main_cache': {'has_data': False, 'cache_size': 0},
                    'details_cache': {'cached_ids': [], 'cache_size': 0}
                }
            
            with open(self.eonet_cache_file, 'r') as f:
                cache_data = json.load(f)
            
            info = {
                'main_cache': {
                    'has_data': 'main_data' in cache_data,
                    'cache_size': 1 if 'main_data' in cache_data else 0,
                    'last_cached': cache_data.get('main_data', {}).get('cached_at', 'Never')
                },
                'details_cache': {
                    'cached_ids': list(cache_data.get('event_details', {}).keys()),
                    'cache_size': len(cache_data.get('event_details', {}))
                },
                'cache_file_size': os.path.getsize(self.eonet_cache_file)
            }
            
            return info
        except Exception as e:
            logger.error(f"Error getting EONET cache info: {e}")
            return {
                'main_cache': {'has_data': False, 'cache_size': 0},
                'details_cache': {'cached_ids': [], 'cache_size': 0}
            }
    
    def get_events_by_category(self, category_id):
        """Get events filtered by category"""
        try:
            all_data = self.get_natural_events()
            
            if not all_data['success']:
                return all_data
            
            filtered_events = [
                event for event in all_data['events']
                if event['category_id'] == category_id
            ]
            
            return {
                'success': True,
                'events': filtered_events,
                'category_id': category_id,
                'total_count': len(filtered_events),
                'filtered_from': all_data['total_count']
            }
            
        except Exception as e:
            logger.error(f"Error filtering events by category: {e}")
            return {
                'success': False,
                'error': str(e),
                'events': [],
                'total_count': 0
            }
