import requests
import numpy as np
from datetime import datetime, timedelta
from skyfield.api import load, EarthSatellite
from skyfield.timelib import Time
import logging
import time
import re
import os
from offline_satellite_data import get_offline_tle_data

class SatelliteTracker:
    def __init__(self, offline_mode=False):
        self.ts = load.timescale()
        self.satellites = {}
        self.categories = self._define_categories()
        self.last_update = None
        self.update_interval = 86400  # 1 day in seconds (24 hours)
        self.offline_mode = offline_mode
        self.load_tle_data()
    
    def _define_categories(self):
        """Define satellite categories with colors"""
        return {
            'ISS': {
                'name': 'International Space Station',
                'color': '#FF6B6B',
                'satellites': []
            },
            'GPS': {
                'name': 'GPS Constellation',
                'color': '#4ECDC4',
                'satellites': []
            },
            'GLONASS': {
                'name': 'GLONASS Navigation',
                'color': '#FF8C42',
                'satellites': []
            },
            'Galileo': {
                'name': 'Galileo Navigation',
                'color': '#6A4C93',
                'satellites': []
            },
            'BeiDou': {
                'name': 'BeiDou Navigation',
                'color': '#F25C54',
                'satellites': []
            },
            'Weather': {
                'name': 'Weather Satellites',
                'color': '#45B7D1',
                'satellites': []
            },
            'Earth_Observation': {
                'name': 'Earth Observation',
                'color': '#52B788',
                'satellites': []
            },
            'Communication': {
                'name': 'Communication Satellites',
                'color': '#96CEB4',
                'satellites': []
            },
            'Starlink': {
                'name': 'Starlink Constellation',
                'color': '#E9C46A',
                'satellites': []
            },
            'OneWeb': {
                'name': 'OneWeb Constellation',
                'color': '#F4A261',
                'satellites': []
            },
            'Iridium': {
                'name': 'Iridium Constellation',
                'color': '#E76F51',
                'satellites': []
            },
            'Scientific': {
                'name': 'Scientific Satellites',
                'color': '#B5838D',
                'satellites': []
            },
            'Military': {
                'name': 'Military Satellites',
                'color': '#8D5524',
                'satellites': []
            },
            'Geostationary': {
                'name': 'Geostationary Satellites',
                'color': '#F77F00',
                'satellites': []
            },
            'Other': {
                'name': 'Other Satellites',
                'color': '#A8A8A8',
                'satellites': []
            }
        }

    def _categorize_satellite(self, name):
        """Categorize satellite based on its name"""
        name_upper = name.upper()
        
        # ISS
        if any(keyword in name_upper for keyword in ['ISS', 'ZARYA', 'INTERNATIONAL SPACE STATION']):
            return 'ISS'
        
        # Navigation systems
        if any(keyword in name_upper for keyword in ['GPS', 'NAVSTAR']):
            return 'GPS'
        if any(keyword in name_upper for keyword in ['GLONASS', 'COSMOS']):
            return 'GLONASS'
        if any(keyword in name_upper for keyword in ['GALILEO', 'GSAT']):
            return 'Galileo'
        if any(keyword in name_upper for keyword in ['BEIDOU', 'COMPASS']):
            return 'BeiDou'
        
        # Commercial constellations
        if 'STARLINK' in name_upper:
            return 'Starlink'
        if any(keyword in name_upper for keyword in ['ONEWEB', 'ONE WEB']):
            return 'OneWeb'
        if 'IRIDIUM' in name_upper:
            return 'Iridium'
        
        # Weather satellites
        if any(keyword in name_upper for keyword in ['NOAA', 'GOES', 'METEOSAT', 'FENGYUN', 'WEATHER']):
            return 'Weather'
        
        # Earth observation
        if any(keyword in name_upper for keyword in ['LANDSAT', 'SENTINEL', 'SPOT', 'WORLDVIEW', 'QUICKBIRD', 'TERRA', 'AQUA']):
            return 'Earth_Observation'
        
        # Communication satellites
        if any(keyword in name_upper for keyword in ['INTELSAT', 'EUTELSAT', 'ASTRA', 'HISPASAT', 'TURKSAT', 'NILESAT', 'ARABSAT']):
            return 'Communication'
        
        # Scientific satellites
        if any(keyword in name_upper for keyword in ['HUBBLE', 'CHANDRA', 'SPITZER', 'KEPLER', 'TESS', 'SWIFT']):
            return 'Scientific'
        
        # Military satellites (basic detection)
        if any(keyword in name_upper for keyword in ['DSP', 'NOSS', 'LACROSSE', 'MENTOR', 'TRUMPET']):
            return 'Military'
        
        # Check for geostationary orbit characteristics (altitude > 35,000 km)
        # This will be determined during position calculation
        
        return 'Other'

    def load_tle_data(self):
        """Load TLE data from online sources or offline file"""
        logging.info("Loading TLE data...")
        
        if self.offline_mode or not self._has_internet():
            logging.info("Using offline TLE data...")
            try:
                # Try to load from saved file first
                if os.path.exists("data/offline_tle_data.txt"):
                    with open("data/offline_tle_data.txt", "r") as f:
                        tle_data = f.read()
                    logging.info("Loaded TLE data from saved file")
                else:
                    # Use sample data
                    tle_data = get_offline_tle_data()
                    logging.info("Using sample TLE data")
                
                self._parse_tle_data(tle_data)
                self.last_update = datetime.now()
                logging.info(f"Loaded {len(self.satellites)} satellites in offline mode")
                return
                
            except Exception as e:
                logging.error(f"Error loading offline data: {e}")
                return
        
        # Online mode - try to fetch from Celestrak
        logging.info("Loading TLE data from online sources...")
        
        # TLE data sources
        tle_sources = [
            [
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle",
            ],
            [
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=noaa&FORMAT=tle",
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=goes&FORMAT=tle",
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle",
            ]
        ]
        
        # Try each source set
        for i, source_set in enumerate(tle_sources, 1):
            logging.info(f"Trying TLE source set {i}")
            total_satellites = 0
            
            for source_url in source_set:
                try:
                    response = requests.get(source_url, timeout=30)
                    response.raise_for_status()
                    
                    satellites_loaded = self._parse_tle_data(response.text)
                    total_satellites += satellites_loaded
                    
                    logging.info(f"Loaded {satellites_loaded} satellites from {source_url}")
                    
                except requests.exceptions.RequestException as e:
                    logging.error(f"Failed to load from {source_url}: {e}")
                    continue
                except Exception as e:
                    logging.error(f"Error parsing TLE data from {source_url}: {e}")
                    continue
            
            if total_satellites > 0:
                logging.info(f"Successfully loaded from {total_satellites} sources in set {i}")
                self.last_update = datetime.now()
                break
        
        logging.info(f"Loaded {len(self.satellites)} satellites")

    def _has_internet(self):
        """Check if internet connection is available"""
        try:
            response = requests.get("https://www.google.com", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _parse_tle_data(self, tle_text):
        """Parse TLE data and create satellite objects"""
        lines = tle_text.strip().split('\n')
        satellites_loaded = 0
        
        # Parse TLE data (3 lines per satellite: name, line 1, line 2)
        for i in range(0, len(lines), 3):
            if i + 2 >= len(lines):
                break
            
            try:
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                
                # Validate TLE format
                if not (line1.startswith('1 ') and line2.startswith('2 ')):
                    continue
                
                # Extract NORAD ID
                norad_id = int(line1[2:7])
                
                # Skip if already loaded
                if norad_id in self.satellites:
                    continue
                
                # Create Skyfield satellite object
                satellite = EarthSatellite(line1, line2, name, self.ts)
                
                # Categorize satellite
                category = self._categorize_satellite(name)
                
                # Store satellite data
                self.satellites[norad_id] = {
                    'name': name,
                    'satellite': satellite,
                    'category': category,
                    'color': self.categories[category]['color'],
                    'line1': line1,
                    'line2': line2,
                    'launch_date': self._extract_launch_date(line1)
                }
                
                # Add to category
                self.categories[category]['satellites'].append(norad_id)
                
                satellites_loaded += 1
                
            except Exception as e:
                logging.error(f"Error parsing TLE for {name if 'name' in locals() else 'unknown'}: {e}")
                continue
        
        return satellites_loaded

    def _extract_launch_date(self, line1):
        """Extract launch date from TLE line 1"""
        try:
            # Extract epoch year and day from TLE
            year_str = line1[18:20]
            day_str = line1[20:32]
            
            # Convert 2-digit year to 4-digit year
            year = int(year_str)
            if year > 57:  # Assuming launches before 2057
                year += 1900
            else:
                year += 2000
            
            # Convert day of year to date
            day_of_year = float(day_str)
            base_date = datetime(year, 1, 1)
            actual_date = base_date + timedelta(days=day_of_year - 1)
            
            return actual_date.strftime('%Y-%m-%d')
        except:
            return '2025-07-22'  # Default date

    def get_satellite_positions(self):
        """Get current positions of all satellites"""
        current_time = self.ts.now()
        positions = []
        
        for norad_id, sat_data in self.satellites.items():
            try:
                satellite = sat_data['satellite']
                
                # Get current position
                geocentric = satellite.at(current_time)
                subpoint = geocentric.subpoint()
                
                # Calculate velocity
                time_delta = self.ts.ut1_jd(current_time.ut1 + 1/86400)  # 1 second later
                future_pos = satellite.at(time_delta)
                future_subpoint = future_pos.subpoint()
                
                # Calculate ground speed
                lat_diff = future_subpoint.latitude.degrees - subpoint.latitude.degrees
                lon_diff = future_subpoint.longitude.degrees - subpoint.longitude.degrees
                velocity = np.sqrt(lat_diff**2 + lon_diff**2) * 111000  # Rough conversion to m/s
                
                # Check if geostationary (update category if needed)
                altitude = subpoint.elevation.km
                if altitude > 35000 and sat_data['category'] == 'Other':
                    sat_data['category'] = 'Geostationary'
                    sat_data['color'] = self.categories['Geostationary']['color']
                
                positions.append({
                    'norad_id': norad_id,
                    'name': sat_data['name'],
                    'latitude': subpoint.latitude.degrees,
                    'longitude': subpoint.longitude.degrees,
                    'altitude': altitude,
                    'velocity': velocity * 3.6,  # Convert to km/h
                    'category': sat_data['category'],
                    'color': sat_data['color'],
                    'launch_date': sat_data['launch_date'],
                    'orbital_period': self._calculate_orbital_period(satellite)
                })
                
            except Exception as e:
                logging.error(f"Error calculating position for satellite {norad_id}: {e}")
                continue
        
        return positions

    def _calculate_orbital_period(self, satellite):
        """Calculate orbital period in minutes"""
        try:
            # Get mean motion from TLE (revolutions per day)
            line2 = satellite.model.line2
            mean_motion = float(line2[52:63])
            
            # Convert to minutes per revolution
            period_minutes = 1440.0 / mean_motion  # 1440 minutes per day
            return period_minutes
            
        except:
            return 90.0  # Default LEO period

    def get_satellite_details(self, norad_id):
        """Get detailed information about a specific satellite"""
        if norad_id not in self.satellites:
            return None
        
        sat_data = self.satellites[norad_id]
        satellite = sat_data['satellite']
        current_time = self.ts.now()
        
        try:
            # Get current position
            geocentric = satellite.at(current_time)
            subpoint = geocentric.subpoint()
            
            return {
                'norad_id': norad_id,
                'name': sat_data['name'],
                'category': sat_data['category'],
                'latitude': subpoint.latitude.degrees,
                'longitude': subpoint.longitude.degrees,
                'altitude': subpoint.elevation.km,
                'launch_date': sat_data['launch_date'],
                'orbital_period': self._calculate_orbital_period(satellite),
                'inclination': satellite.model.inclo * 180 / np.pi,  # Convert from radians
                'eccentricity': satellite.model.ecco,
                'color': sat_data['color']
            }
        except Exception as e:
            logging.error(f"Error getting details for satellite {norad_id}: {e}")
            return None

    def get_satellite_orbit_path(self, norad_id, duration_hours=3):
        """Get orbit path for a satellite over specified duration"""
        if norad_id not in self.satellites:
            return []
        
        satellite = self.satellites[norad_id]['satellite']
        current_time = self.ts.now()
        
        # Generate time points for orbit path
        time_points = []
        minutes = duration_hours * 60
        for i in range(0, minutes, 5):  # Every 5 minutes
            t = self.ts.ut1_jd(current_time.ut1 + i / (24 * 60))
            time_points.append(t)
        
        orbit_points = []
        for t in time_points:
            try:
                geocentric = satellite.at(t)
                position = geocentric.position.km
                orbit_points.append({
                    'x': position[0],
                    'y': position[1],
                    'z': position[2],
                    'time': t.ut1_iso()
                })
            except Exception as e:
                logging.error(f"Error calculating orbit point: {e}")
                continue
        
        return orbit_points

    def get_future_ground_track(self, norad_id, duration_hours=3):
        """Get future ground track for a satellite"""
        if norad_id not in self.satellites:
            return []
        
        satellite = self.satellites[norad_id]['satellite']
        current_time = self.ts.now()
        
        ground_track_points = []
        minutes = duration_hours * 60
        
        for i in range(0, minutes, 2):  # Every 2 minutes
            try:
                t = self.ts.ut1_jd(current_time.ut1 + i / (24 * 60))
                geocentric = satellite.at(t)
                subpoint = geocentric.subpoint()
                
                ground_track_points.append({
                    'latitude': subpoint.latitude.degrees,
                    'longitude': subpoint.longitude.degrees,
                    'altitude': subpoint.elevation.km,
                    'time': t.ut1_iso()
                })
            except Exception as e:
                logging.error(f"Error calculating ground track point: {e}")
                continue
        
        return ground_track_points

    def get_satellite_categories(self):
        """Get all satellite categories with counts"""
        categories = {}
        for cat_id, cat_info in self.categories.items():
            categories[cat_id] = {
                'name': cat_info['name'],
                'color': cat_info['color'],
                'count': len(cat_info['satellites'])
            }
        return categories

    def get_current_time(self):
        """Get current time in ISO format"""
        return datetime.now().isoformat() + 'Z'

    def refresh_tle_data(self):
        """Force refresh of TLE data"""
        self.satellites.clear()
        for category in self.categories.values():
            category['satellites'].clear()
        self.load_tle_data()

    def get_next_passes(self, norad_id, observer_lat, observer_lon, observer_alt=0):
        """Get next passes of satellite over observer location"""
        if norad_id not in self.satellites:
            return []
        
        try:
            satellite = self.satellites[norad_id]['satellite']
            
            # Create observer location
            from skyfield.api import wgs84
            observer = wgs84.latlon(observer_lat, observer_lon, elevation_m=observer_alt)
            
            # Get current time and next 24 hours
            current_time = self.ts.now()
            end_time = self.ts.ut1_jd(current_time.ut1 + 1)  # 24 hours later
            
            # Find passes (simplified - just check visibility every hour)
            passes = []
            for hour in range(24):
                t = self.ts.ut1_jd(current_time.ut1 + hour/24)
                try:
                    difference = satellite - observer
                    topocentric = difference.at(t)
                    alt, az, distance = topocentric.altaz()
                    
                    if alt.degrees > 10:  # Visible above 10 degrees
                        passes.append({
                            'time': t.ut1_iso(),
                            'altitude': alt.degrees,
                            'azimuth': az.degrees,
                            'distance': distance.km
                        })
                except:
                    continue
            
            return passes
            
        except Exception as e:
            logging.error(f"Error calculating passes: {e}")
            return []