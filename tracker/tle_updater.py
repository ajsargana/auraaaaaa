
import os
import json
import requests
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class TLEUpdater:
    def __init__(self, update_interval_hours=48):
        """
        Initialize TLE updater with smart caching

        Args:
            update_interval_hours: How often to fetch fresh TLE data (default: 48 hours / 2 days)
                                  - 24 hours = daily updates (aggressive)
                                  - 48 hours = every 2 days (recommended)
                                  - 720 hours = 30 days (prototype mode - no updates)
        """
        self.tle_file_path = os.path.join('cache', 'tle_data.txt')
        self.metadata_file_path = os.path.join('cache', 'cache_metadata.json')

        # TLE updates enabled
        self.update_interval_hours = update_interval_hours
        self.update_interval_days = self.update_interval_hours / 24

        # Ensure cache directory exists
        os.makedirs('cache', exist_ok=True)

        logger.info(f"📡 TLE Updater initialized:")
        logger.info(f"   Update interval: {self.update_interval_hours} hours ({self.update_interval_days:.1f} days)")
        logger.info(f"   Cache file: {self.tle_file_path}")
    
    def should_update(self):
        """Check if TLE data should be updated (older than 2 days)"""
        try:
            if not os.path.exists(self.tle_file_path):
                logger.info("TLE file not found - update required")
                return True

            if not os.path.exists(self.metadata_file_path):
                logger.info("Metadata file not found - update required")
                return True

            with open(self.metadata_file_path, 'r') as f:
                metadata = json.load(f)

            last_update = datetime.fromisoformat(metadata.get('last_update', '2000-01-01T00:00:00+00:00'))
            now = datetime.now(timezone.utc)

            hours_since_update = (now - last_update).total_seconds() / 3600
            days_since_update = hours_since_update / 24

            logger.info(f"⏰ TLE data age: {hours_since_update:.1f} hours ({days_since_update:.1f} days)")
            logger.info(f"   Last update: {last_update.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            logger.info(f"   Update interval: {self.update_interval_days} days")

            needs_update = days_since_update >= self.update_interval_days

            if needs_update:
                logger.info(f"✅ TLE data is stale - update needed")
            else:
                logger.info(f"✅ TLE data is fresh - no update needed")

            return needs_update

        except Exception as e:
            logger.error(f"Error checking update time: {e}")
            return True

    def update_if_needed(self):
        """Smart update: Only fetch new TLE data if cache is stale"""
        if self.should_update():
            logger.info("📡 Fetching fresh TLE data from online sources...")
            return self.update_tle_data()
        else:
            logger.info("📦 Using cached TLE data (still fresh)")
            return True
    
    def update_tle_data(self):
        """Download fresh TLE data from online sources"""
        try:
            logger.info("Updating TLE data from online sources...")
            
            # Full TLE source list — GEO, IGSO, LEO constellations, EO priority
            tle_sources = [
                # Full active catalog (covers GEO + IGSO + all LEO)
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle',

                # GEO communication satellites
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=geo&FORMAT=tle',
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=intelsat&FORMAT=tle',
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=ses&FORMAT=tle',
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=telesat&FORMAT=tle',
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium&FORMAT=tle',
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle',

                # Navigation constellations
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=tle',
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=galileo&FORMAT=tle',
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=beidou&FORMAT=tle',
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=glonass-ops&FORMAT=tle',

                # LEO constellations
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle',

                # Earth observation & science
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle',
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle',
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=science&FORMAT=tle',
                'https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle',

                # Priority EO individual TLEs (guarantee they're present)
                'https://celestrak.org/NORAD/elements/gp.php?CATNR=39084&FORMAT=tle',   # Landsat 8
                'https://celestrak.org/NORAD/elements/gp.php?CATNR=49260&FORMAT=tle',   # Landsat 9
                'https://celestrak.org/NORAD/elements/gp.php?CATNR=39634&FORMAT=tle',   # Sentinel-1A
                'https://celestrak.org/NORAD/elements/gp.php?CATNR=40697&FORMAT=tle',   # Sentinel-2A
                'https://celestrak.org/NORAD/elements/gp.php?CATNR=42063&FORMAT=tle',   # Sentinel-2B
                'https://celestrak.org/NORAD/elements/gp.php?CATNR=43437&FORMAT=tle',   # Sentinel-3A
                'https://celestrak.org/NORAD/elements/gp.php?CATNR=43485&FORMAT=tle',   # Sentinel-3B
                'https://celestrak.org/NORAD/elements/gp.php?CATNR=44427&FORMAT=tle',   # Sentinel-5P
                'https://celestrak.org/NORAD/elements/gp.php?CATNR=43013&FORMAT=tle',   # Sentinel-6MF
                'https://celestrak.org/NORAD/elements/gp.php?CATNR=32060&FORMAT=tle',   # WorldView-1
                'https://celestrak.org/NORAD/elements/gp.php?CATNR=35946&FORMAT=tle',   # WorldView-2
                'https://celestrak.org/NORAD/elements/gp.php?CATNR=40115&FORMAT=tle',   # WorldView-3
            ]

            all_tle_data = []
            satellites_loaded = 0
            seen_norad_ids = set()  # deduplicate across sources

            for source_url in tle_sources:
                try:
                    logger.info(f"Fetching TLE data from: {source_url}")
                    response = requests.get(source_url, timeout=30)
                    response.raise_for_status()

                    tle_lines = response.text.strip().split('\n')
                    source_satellites = 0

                    i = 0
                    while i < len(tle_lines) - 2:
                        try:
                            name_line = tle_lines[i].strip()
                            line1 = tle_lines[i + 1].strip()
                            line2 = tle_lines[i + 2].strip()

                            if (len(line1) == 69 and len(line2) == 69 and
                                    line1.startswith('1') and line2.startswith('2')):

                                norad_id = int(line1[2:7])
                                if norad_id not in seen_norad_ids:
                                    seen_norad_ids.add(norad_id)
                                    all_tle_data.extend([name_line, line1, line2])
                                    source_satellites += 1
                                    satellites_loaded += 1

                            i += 3

                        except (IndexError, ValueError):
                            i += 1
                            continue

                    logger.info(f"Loaded {source_satellites} new satellites from {source_url}")

                except requests.RequestException as e:
                    logger.warning(f"Failed to fetch from {source_url}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing {source_url}: {e}")
                    continue
            
            if satellites_loaded > 0:
                # Validate that priority satellites are present
                priority_satellites = self._validate_priority_satellites(all_tle_data)
                
                # Write TLE data to file
                with open(self.tle_file_path, 'w') as f:
                    f.write('\n'.join(all_tle_data))
                
                # Update metadata
                metadata = {
                    'last_update': datetime.now(timezone.utc).isoformat(),
                    'satellites_count': satellites_loaded,
                    'sources_used': len(tle_sources),
                    'priority_satellites': priority_satellites
                }
                
                with open(self.metadata_file_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"Successfully updated TLE data with {satellites_loaded} satellites")
                logger.info(f"Priority satellites included: {len(priority_satellites['found'])}/{len(priority_satellites['expected'])}")
                if priority_satellites['missing']:
                    logger.warning(f"Missing priority satellites: {', '.join(priority_satellites['missing'])}")
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
    
    def _validate_priority_satellites(self, tle_data):
        """Validate that priority Earth observation satellites are present"""
        priority_missions = {
            'LANDSAT 8': 39084,
            'LANDSAT 9': 49260,
            'SENTINEL-1A': 39634,
            'SENTINEL-1B': 41456,
            'SENTINEL-2A': 40697,
            'SENTINEL-2B': 42063,
            'SENTINEL-3A': 43437,
            'SENTINEL-3B': 43485,
            'SENTINEL-5P': 44427,
            'SENTINEL-6MF': 46984,
            'WORLDVIEW-1': 32060,
            'WORLDVIEW-2': 35946,
            'WORLDVIEW-3': 40115
        }
        
        found_satellites = []
        missing_satellites = []
        
        # Convert TLE data to string for searching
        tle_string = '\n'.join(tle_data)
        
        for name, norad_id in priority_missions.items():
            # Check if satellite is present by NORAD ID in TLE line 1
            if f'1 {norad_id}U' in tle_string or f'1 {norad_id} ' in tle_string:
                found_satellites.append(name)
            else:
                missing_satellites.append(name)
        
        return {
            'expected': list(priority_missions.keys()),
            'found': found_satellites,
            'missing': missing_satellites
        }
    
    def get_cache_info(self):
        """Get information about the TLE cache"""
        try:
            info = {
                'file_exists': os.path.exists(self.tle_file_path),
                'metadata_exists': os.path.exists(self.metadata_file_path),
                'last_update': None,
                'satellites_count': 0,
                'days_old': None,
                'priority_satellites': None
            }
            
            if info['metadata_exists']:
                with open(self.metadata_file_path, 'r') as f:
                    metadata = json.load(f)
                
                last_update = datetime.fromisoformat(metadata.get('last_update', '2000-01-01T00:00:00+00:00'))
                info['last_update'] = last_update.isoformat()
                info['satellites_count'] = metadata.get('satellites_count', 0)
                info['days_old'] = (datetime.now(timezone.utc) - last_update).days
                info['priority_satellites'] = metadata.get('priority_satellites', None)
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return None
