#!/usr/bin/env python3

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
        self.ts = load.timescale()
        self.last_update = None
        
    def load_tle_data(self):
        """Load a small sample of TLE data for testing"""
        try:
            # Sample TLE data for testing - ISS and a few other satellites
            sample_tle_data = [
                ("ISS (ZARYA)", 
                 "1 25544U 98067A   25212.50000000  .00002182  00000-0  40864-4 0  9992",
                 "2 25544  51.6416 339.7760 0003835 106.1678 254.0098 15.48919103123456"),
                ("HUBBLE SPACE TELESCOPE",
                 "1 20580U 90037B   25212.50000000  .00000583  00000-0  37198-4 0  9996", 
                 "2 20580  28.4691 108.5182 0002969 321.7771  38.2473 15.09292105654321"),
                ("NOAA 19",
                 "1 33591U 09005A   25212.50000000  .00000012  00000-0  25806-4 0  9990",
                 "2 33591  99.1890 161.3479 0013649 273.9959  86.0133 14.12501637789123"),
                ("GPS BIIR-2  (PRN 13)",
                 "1 24876U 97035A   25212.50000000 -.00000079  00000-0  00000+0 0  9994",
                 "2 24876  55.4522 128.7625 0048961 266.2523  93.0041  2.00568180456789"),
                ("STARLINK-1007",
                 "1 44713U 19074A   25212.50000000  .00001247  00000-0  95842-4 0  9998",
                 "2 44713  53.0534 123.4567 0001234  89.1234 270.9876 15.05123456123456")
            ]
            
            logger.info(f"Loading {len(sample_tle_data)} sample satellites...")
            
            satellites_loaded = 0
            for name, line1, line2 in sample_tle_data:
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
                    
                    # Skip satellites with invalid positions
                    if not (lat == lat and lon == lon and alt == alt):  # NaN check
                        logger.warning(f"Skipping {name} due to invalid position")
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
                    logger.info(f"Loaded satellite: {name} at {lat:.2f}, {lon:.2f}, {alt:.2f}km")
                    
                except Exception as sat_error:
                    logger.error(f"Error loading satellite {name}: {sat_error}")
                    continue
                    
            logger.info(f"Successfully loaded {satellites_loaded} satellites from sample data")
            self.last_update = datetime.now(timezone.utc)
            return True
            
        except Exception as e:
            logger.error(f"Error loading sample satellite data: {e}")
            return False
    
    def get_satellites(self):
        """Return all satellites data"""
        satellites_list = []
        for sat_data in self.satellites.values():
            # Create a copy without the skyfield object
            sat_dict = {
                'norad_id': sat_data['norad_id'],
                'name': sat_data['name'],
                'latitude': sat_data['latitude'],
                'longitude': sat_data['longitude'],
                'altitude': sat_data['altitude'],
                'category': sat_data['category'],
                'color': sat_data['color']
            }
            satellites_list.append(sat_dict)
        return satellites_list
    
    def update_positions(self):
        """Update satellite positions for real-time movement"""
        try:
            t = self.ts.now()
            updated_count = 0
            
            for norad_id, sat_data in self.satellites.items():
                try:
                    satellite = sat_data['satellite_obj']
                    geocentric = satellite.at(t)
                    
                    # Get position relative to Earth
                    from skyfield.api import wgs84
                    subpoint = wgs84.subpoint(geocentric)
                    
                    # Update position data with NaN checking
                    lat = float(subpoint.latitude.degrees)
                    lon = float(subpoint.longitude.degrees)
                    alt = float(subpoint.elevation.km)
                    
                    # Only update if values are valid numbers and reasonable
                    if (lat == lat and lon == lon and alt == alt and  # NaN check
                        -90 <= lat <= 90 and -180 <= lon <= 180 and 0 < alt < 50000):
                        
                        sat_data['latitude'] = lat
                        sat_data['longitude'] = lon
                        sat_data['altitude'] = alt
                        updated_count += 1
                        
                except Exception as sat_error:
                    logger.warning(f"Error updating position for satellite {norad_id}: {sat_error}")
                    continue
                
            logger.info(f"Updated positions for {updated_count} satellites")
            
        except Exception as e:
            logger.error(f"Error updating satellite positions: {e}")
    
    def get_status(self):
        """Return system status"""
        return {
            'satellites_loaded': len(self.satellites),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'categories': len(set(sat['category'] for sat in self.satellites.values()))
        }
    
    def get_satellite_data(self):
        """Return satellites data - alias for get_satellites()"""
        self.update_positions()  # Update positions before returning data
        return self.get_satellites()
    
    def refresh_data(self):
        """Refresh satellite data by reloading TLE data"""
        logger.info("Refreshing satellite data...")
        self.satellites.clear()
        return self.load_tle_data()
    
    def get_satellite_by_id(self, norad_id):
        """Get specific satellite by NORAD ID"""
        if norad_id in self.satellites:
            self.update_positions()  # Update positions before returning data
            # Return data without the satellite object for JSON serialization
            sat_data = self.satellites[norad_id]
            return {
                'norad_id': sat_data['norad_id'],
                'name': sat_data['name'],
                'latitude': sat_data['latitude'],
                'longitude': sat_data['longitude'],
                'altitude': sat_data['altitude'],
                'category': sat_data['category'],
                'color': sat_data['color'],
                # Add detailed satellite information for the UI
                'orbit': {
                    'altitude': sat_data['altitude'],
                    'inclination': 0.0,  # Placeholder - would need orbital elements for real calculation
                    'period': 90.0,  # Placeholder
                    'velocity': 7.8,  # Placeholder
                    'orbit_type': 'LEO' if sat_data['altitude'] < 2000 else 'MEO' if sat_data['altitude'] < 35786 else 'GEO'
                },
                'position': {
                    'latitude': sat_data['latitude'],
                    'longitude': sat_data['longitude'],
                    'country': 'Unknown',  # Placeholder
                    'visibility': 'Visible' if sat_data['altitude'] < 1000 else 'Not Visible'
                },
                'technical': {
                    'norad_id': sat_data['norad_id'],
                    'launch_date': 'Unknown',  # Placeholder
                    'type': sat_data['category'].replace('_', ' ').title(),
                    'agency': 'Unknown',  # Placeholder
                    'status': 'Active'
                }
            }
        return None
    
    def get_categories(self):
        """Return satellite categories with counts"""
        from collections import defaultdict
        category_counts = defaultdict(int)
        
        for sat_data in self.satellites.values():
            category_counts[sat_data['category']] += 1
        
        # Define category colors directly
        category_colors = {
            'iss': '#FF6B6B',
            'scientific': '#9B59B6', 
            'weather': '#45B7D1',
            'gps': '#4ECDC4',
            'starlink': '#E9C46A',
            'communication': '#F39C12',
            'military': '#E74C3C',
            'other': '#95A5A6'
        }
        
        categories = {}
        for category, count in category_counts.items():
            categories[category] = {
                'name': category.replace('_', ' ').title(),
                'color': category_colors.get(category, '#64b5f6'),
                'count': count
            }
        
        return categories