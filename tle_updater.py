
import os
import json
import requests
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class TLEUpdater:
    def __init__(self):
        self.tle_file_path = os.path.join('cache', 'tle_data.txt')
        self.metadata_file_path = os.path.join('cache', 'cache_metadata.json')
        self.update_interval_days = 2
        
        # Ensure cache directory exists
        os.makedirs('cache', exist_ok=True)
    
    def should_update(self):
        """Check if TLE data should be updated (older than 2 days)"""
        try:
            if not os.path.exists(self.metadata_file_path):
                return True
                
            with open(self.metadata_file_path, 'r') as f:
                metadata = json.load(f)
            
            last_update = datetime.fromisoformat(metadata.get('last_update', '2000-01-01T00:00:00+00:00'))
            now = datetime.now(timezone.utc)
            
            days_since_update = (now - last_update).days
            logger.info(f"Days since last TLE update: {days_since_update}")
            
            return days_since_update >= self.update_interval_days
            
        except Exception as e:
            logger.error(f"Error checking update time: {e}")
            return True
    
    def update_tle_data(self):
        """Download fresh TLE data from online sources"""
        try:
            logger.info("Updating TLE data from online sources...")
            
            # List of TLE data sources
            tle_sources = [
                'https://celestrak.com/NORAD/elements/stations.txt',      # ISS and space stations
                'https://celestrak.com/NORAD/elements/visual.txt',       # Bright satellites
                'https://celestrak.com/NORAD/elements/weather.txt',      # Weather satellites
                'https://celestrak.com/NORAD/elements/science.txt',      # Science satellites
                'https://celestrak.com/NORAD/elements/gps-ops.txt',      # GPS satellites
                'https://celestrak.com/NORAD/elements/galileo.txt',      # Galileo satellites
                'https://celestrak.com/NORAD/elements/beidou.txt',       # BeiDou satellites
                'https://celestrak.com/NORAD/elements/glonass-ops.txt',  # GLONASS satellites
                'https://celestrak.com/NORAD/elements/starlink.txt',     # Starlink satellites
            ]
            
            all_tle_data = []
            satellites_loaded = 0
            
            for source_url in tle_sources:
                try:
                    logger.info(f"Fetching TLE data from: {source_url}")
                    response = requests.get(source_url, timeout=30)
                    response.raise_for_status()
                    
                    tle_lines = response.text.strip().split('\n')
                    source_satellites = 0
                    
                    # Process TLE data in groups of 3 lines (name, line1, line2)
                    i = 0
                    while i < len(tle_lines) - 2:
                        try:
                            name_line = tle_lines[i].strip()
                            line1 = tle_lines[i + 1].strip()
                            line2 = tle_lines[i + 2].strip()
                            
                            # Validate TLE format
                            if (len(line1) == 69 and len(line2) == 69 and 
                                line1.startswith('1') and line2.startswith('2')):
                                
                                all_tle_data.extend([name_line, line1, line2])
                                source_satellites += 1
                                satellites_loaded += 1
                            
                            i += 3
                            
                        except (IndexError, ValueError):
                            i += 1
                            continue
                    
                    logger.info(f"Loaded {source_satellites} satellites from {source_url}")
                    
                except requests.RequestException as e:
                    logger.warning(f"Failed to fetch from {source_url}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing {source_url}: {e}")
                    continue
            
            if satellites_loaded > 0:
                # Write TLE data to file
                with open(self.tle_file_path, 'w') as f:
                    f.write('\n'.join(all_tle_data))
                
                # Update metadata
                metadata = {
                    'last_update': datetime.now(timezone.utc).isoformat(),
                    'satellites_count': satellites_loaded,
                    'sources_used': len(tle_sources)
                }
                
                with open(self.metadata_file_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"Successfully updated TLE data with {satellites_loaded} satellites")
                return True
            else:
                logger.error("No valid TLE data was downloaded")
                return False
                
        except Exception as e:
            logger.error(f"Error updating TLE data: {e}")
            return False
    
    def ensure_tle_data(self):
        """Ensure TLE data is available and up-to-date"""
        try:
            # Check if we need to update
            if self.should_update():
                logger.info("TLE data is outdated, updating...")
                if self.update_tle_data():
                    logger.info("TLE data successfully updated")
                else:
                    logger.warning("Failed to update TLE data, using existing data if available")
            else:
                logger.info("TLE data is current, no update needed")
            
            # Verify that TLE data file exists
            if not os.path.exists(self.tle_file_path):
                logger.error("No TLE data file found, forcing update...")
                return self.update_tle_data()
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring TLE data: {e}")
            return False
    
    def get_cache_info(self):
        """Get information about the TLE cache"""
        try:
            info = {
                'file_exists': os.path.exists(self.tle_file_path),
                'metadata_exists': os.path.exists(self.metadata_file_path),
                'last_update': None,
                'satellites_count': 0,
                'days_old': None
            }
            
            if info['metadata_exists']:
                with open(self.metadata_file_path, 'r') as f:
                    metadata = json.load(f)
                
                last_update = datetime.fromisoformat(metadata.get('last_update', '2000-01-01T00:00:00+00:00'))
                info['last_update'] = last_update.isoformat()
                info['satellites_count'] = metadata.get('satellites_count', 0)
                info['days_old'] = (datetime.now(timezone.utc) - last_update).days
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return None
