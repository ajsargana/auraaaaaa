
"""
Launch Data Module - Fetches upcoming rocket launches from Launch Library 2 API
Free API, no key required: https://ll.thespacedevs.com/2.2.0/
"""
import requests
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
import json
import os

logger = logging.getLogger(__name__)

class LaunchDataModule:
    def __init__(self):
        self.api_base = "https://ll.thespacedevs.com/2.2.0"
        self.cache_file = "cache/launches_cache.json"
        self.cache_duration = 3600  # 1 hour cache
        
        # Ensure cache directory exists
        os.makedirs("cache", exist_ok=True)
    
    def _get_from_cache(self) -> Optional[Dict]:
        """Get cached launch data if still valid"""
        try:
            if not os.path.exists(self.cache_file):
                return None
            
            with open(self.cache_file, 'r') as f:
                cached = json.load(f)
            
            cached_time = datetime.fromisoformat(cached.get('cached_at', '2000-01-01'))
            age = (datetime.now(timezone.utc) - cached_time).total_seconds()
            
            if age < self.cache_duration:
                logger.info(f"Using cached launch data (age: {age:.0f}s)")
                return cached
            
            return None
        except Exception as e:
            logger.error(f"Error reading launch cache: {e}")
            return None
    
    def _save_to_cache(self, data: Dict):
        """Save launch data to cache"""
        try:
            data['cached_at'] = datetime.now(timezone.utc).isoformat()
            with open(self.cache_file, 'w') as f:
                json.dump(data, f)
            logger.info("Launch data cached successfully")
        except Exception as e:
            logger.error(f"Error saving launch cache: {e}")
    
    def get_upcoming_launches(self, limit: int = 50) -> Dict:
        """Get upcoming rocket launches"""
        try:
            # Check cache first
            cached = self._get_from_cache()
            if cached:
                return cached
            
            logger.info("Fetching upcoming launches from Launch Library 2 API...")
            
            url = f"{self.api_base}/launch/upcoming/"
            params = {
                'limit': limit,
                'mode': 'detailed'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            launches = data.get('results', [])
            
            processed_launches = []
            for launch in launches:
                processed_launches.append({
                    'id': launch.get('id'),
                    'name': launch.get('name'),
                    'net': launch.get('net'),  # No Earlier Than time
                    'window_start': launch.get('window_start'),
                    'window_end': launch.get('window_end'),
                    'status': launch.get('status', {}).get('name'),
                    'rocket': {
                        'name': launch.get('rocket', {}).get('configuration', {}).get('name'),
                        'family': launch.get('rocket', {}).get('configuration', {}).get('family'),
                        'variant': launch.get('rocket', {}).get('configuration', {}).get('variant'),
                    },
                    'mission': {
                        'name': launch.get('mission', {}).get('name') if launch.get('mission') else 'Unknown',
                        'type': launch.get('mission', {}).get('type') if launch.get('mission') else 'Unknown',
                        'description': launch.get('mission', {}).get('description') if launch.get('mission') else ''
                    },
                    'pad': {
                        'name': launch.get('pad', {}).get('name'),
                        'location': launch.get('pad', {}).get('location', {}).get('name'),
                        'country': launch.get('pad', {}).get('location', {}).get('country_code')
                    },
                    'agency': {
                        'name': launch.get('launch_service_provider', {}).get('name'),
                        'type': launch.get('launch_service_provider', {}).get('type'),
                        'country': launch.get('launch_service_provider', {}).get('country_code')
                    },
                    'probability': launch.get('probability'),
                    'image': launch.get('image'),
                    'webcast_live': launch.get('webcast_live'),
                    'video_url': launch.get('vid_urls', [{}])[0].get('url') if launch.get('vid_urls') else None
                })
            
            result = {
                'success': True,
                'launches': processed_launches,
                'total_count': len(processed_launches)
            }
            
            # Cache the result
            self._save_to_cache(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching launch data: {e}")
            return {
                'success': False,
                'error': str(e),
                'launches': [],
                'total_count': 0
            }
    
    def get_launch_analytics(self) -> Dict:
        """Get analytics about launches"""
        try:
            launches_data = self.get_upcoming_launches(limit=100)
            
            if not launches_data['success']:
                return {'success': False, 'error': 'Failed to fetch launches'}
            
            launches = launches_data['launches']
            
            # Analytics
            rocket_counts = {}
            country_counts = {}
            agency_counts = {}
            location_counts = {}
            mission_types = {}
            
            for launch in launches:
                # Rocket analytics
                rocket_name = launch['rocket']['name']
                rocket_counts[rocket_name] = rocket_counts.get(rocket_name, 0) + 1
                
                # Country analytics
                country = launch['pad']['country']
                country_counts[country] = country_counts.get(country, 0) + 1
                
                # Agency analytics
                agency = launch['agency']['name']
                agency_counts[agency] = agency_counts.get(agency, 0) + 1
                
                # Location analytics
                location = launch['pad']['location']
                location_counts[location] = location_counts.get(location, 0) + 1
                
                # Mission type analytics
                mission_type = launch['mission']['type']
                mission_types[mission_type] = mission_types.get(mission_type, 0) + 1
            
            return {
                'success': True,
                'analytics': {
                    'total_upcoming': len(launches),
                    'by_rocket': dict(sorted(rocket_counts.items(), key=lambda x: x[1], reverse=True)),
                    'by_country': dict(sorted(country_counts.items(), key=lambda x: x[1], reverse=True)),
                    'by_agency': dict(sorted(agency_counts.items(), key=lambda x: x[1], reverse=True)),
                    'by_location': dict(sorted(location_counts.items(), key=lambda x: x[1], reverse=True)),
                    'by_mission_type': dict(sorted(mission_types.items(), key=lambda x: x[1], reverse=True))
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating launch analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
