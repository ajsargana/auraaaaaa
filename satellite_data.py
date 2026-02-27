"""
Simplified satellite data module using static TLE data from tle_data.txt
"""
import os
import logging
from skyfield.api import load, EarthSatellite
from datetime import datetime, timezone
from satellite_categories import categorize_satellite

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SatelliteDataManager:
    def __init__(self):
        self.satellites = {}
        self.tle_file_path = os.path.join('cache', 'tle_data.txt')
        self.ts = load.timescale()
        self.last_update = None
        
    def load_tle_data(self):
        """Load TLE data from static tle_data.txt file"""
        try:
            if not os.path.exists(self.tle_file_path):
                logger.error(f"TLE data file not found: {self.tle_file_path}")
                return False
                
            logger.info(f"Loading TLE data from {self.tle_file_path}...")
            
            with open(self.tle_file_path, 'r') as f:
                lines = f.readlines()
            
            satellites_loaded = 0
            max_satellites = 500  # Limit to 500 satellites for performance
            i = 0
            
            while i < len(lines) - 2 and satellites_loaded < max_satellites:
                # Skip empty lines
                if not lines[i].strip():
                    i += 1
                    continue
                    
                try:
                    # Parse TLE format: name line, line1, line2
                    name = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()
                    
                    # Validate TLE format
                    if len(line1) == 69 and len(line2) == 69 and line1.startswith('1') and line2.startswith('2'):
                        try:
                            # Extract NORAD ID
                            norad_id = int(line1[2:7])
                            
                            # Create satellite object
                            satellite = EarthSatellite(line1, line2, name, self.ts)
                            
                            # Get current position with error handling
                            t = self.ts.now()
                            geocentric = satellite.at(t)
                            
                            # Get position relative to Earth
                            from skyfield.api import wgs84
                            subpoint = wgs84.subpoint(geocentric)
                            
                            # Extract position values
                            lat = float(subpoint.latitude.degrees)
                            lon = float(subpoint.longitude.degrees)
                            alt = float(subpoint.elevation.km)
                            
                            # Skip satellites with invalid positions or extreme altitudes
                            if not (lat == lat and lon == lon and alt == alt):  # NaN check
                                continue
                            if alt < 0 or alt > 50000:  # Reasonable altitude bounds
                                continue
                                
                            # Categorize satellite
                            category, color = categorize_satellite(name)
                            
                            self.satellites[norad_id] = {
                                'norad_id': norad_id,
                                'name': name.strip(),
                                'latitude': lat,
                                'longitude': lon,
                                'altitude': alt,
                                'category': category,
                                'color': color,
                                'satellite_obj': satellite
                            }
                            
                            satellites_loaded += 1
                            
                            # Progress logging every 100 satellites
                            if satellites_loaded % 100 == 0:
                                logger.info(f"Loaded {satellites_loaded} satellites...")
                            
                        except Exception as sat_error:
                            # Skip problematic satellites silently
                            continue
                        
                    i += 3
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Skipping invalid TLE data at line {i}: {e}")
                    i += 1
                    continue
            
            logger.info(f"Successfully loaded {satellites_loaded} satellites from TLE data")
            self.last_update = datetime.now(timezone.utc)
            return True
            
        except Exception as e:
            logger.error(f"Error loading TLE data: {e}")
            return False
    
    def update_positions(self):
        """Update satellite positions using current time"""
        if not self.satellites:
            return
            
        try:
            t = self.ts.now()
            
            for norad_id, sat_data in self.satellites.items():
                satellite = sat_data['satellite_obj']
                geocentric = satellite.at(t)
                
                # Get position relative to Earth
                from skyfield.api import wgs84
                subpoint = wgs84.subpoint(geocentric)
                
                # Update position data with NaN checking
                lat = float(subpoint.latitude.degrees)
                lon = float(subpoint.longitude.degrees)
                alt = float(subpoint.elevation.km)
                
                # Only update if values are valid numbers
                if lat == lat and lon == lon and alt == alt:  # NaN check
                    sat_data['latitude'] = lat
                    sat_data['longitude'] = lon
                    sat_data['altitude'] = alt
                
        except Exception as e:
            logger.error(f"Error updating satellite positions: {e}")
    
    def get_satellite_data(self):
        """Get all satellite data as a list"""
        self.update_positions()
        # Return data without the satellite object for JSON serialization
        result = []
        for sat_data in self.satellites.values():
            data_copy = sat_data.copy()
            data_copy.pop('satellite_obj', None)  # Remove non-serializable object
            result.append(data_copy)
        return result
    
    def get_satellite_by_id(self, norad_id):
        """Get specific satellite by NORAD ID"""
        if norad_id in self.satellites:
            self.update_positions()
            # Return data without the satellite object for JSON serialization
            data_copy = self.satellites[norad_id].copy()
            data_copy.pop('satellite_obj', None)  # Remove non-serializable object
            return data_copy
        return None
    
    def get_categories(self):
        """Get satellite categories with counts"""
        categories = {}
        
        for sat_data in self.satellites.values():
            category = sat_data['category']
            if category not in categories:
                categories[category] = {
                    'name': category.replace('_', ' ').title(),
                    'color': sat_data['color'],
                    'count': 0
                }
            categories[category]['count'] += 1
            
        return categories