"""
Satellite data management and TLE parsing
Separated for better organization and performance
"""

import numpy as np
import logging
from datetime import datetime, timedelta
from skyfield.api import load, EarthSatellite

class SatelliteData:
    def __init__(self, categories_manager):
        self.ts = load.timescale()
        self.satellites = {}
        self.categories = categories_manager
        
    def parse_tle_data(self, tle_text):
        """Parse TLE data and create satellite objects"""
        lines = tle_text.strip().split('\n')
        satellites_loaded = 0
        
        # Clear existing categories
        self.categories.clear_all_categories()
        
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
                
                # Calculate initial position to determine category
                try:
                    current_time = self.ts.now()
                    geocentric = satellite.at(current_time)
                    subpoint = geocentric.subpoint()
                    altitude = subpoint.elevation.km
                except:
                    altitude = None
                
                # Categorize satellite
                category = self.categories.categorize_satellite(name, altitude)
                
                # Store satellite data
                self.satellites[norad_id] = {
                    'name': name,
                    'satellite': satellite,
                    'category': category,
                    'color': self.categories.get_category_info(category)['color'],
                    'line1': line1,
                    'line2': line2,
                    'launch_date': self._extract_launch_date(line1),
                    'last_position': None,  # Cache last position for smooth movement
                    'last_update': None
                }
                
                # Add to category
                self.categories.add_satellite_to_category(category, norad_id)
                
                satellites_loaded += 1
                
            except Exception as e:
                logging.error(f"Error parsing TLE for {name if 'name' in locals() else 'unknown'}: {e}")
                continue
        
        logging.info(f"Parsed {satellites_loaded} satellites from TLE data")
        return satellites_loaded
    
    def _extract_launch_date(self, line1):
        """Extract launch date from TLE line 1"""
        try:
            year_str = line1[18:20]
            day_str = line1[20:32]
            
            year = int(year_str)
            if year > 57:
                year += 1900
            else:
                year += 2000
            
            day_of_year = float(day_str)
            base_date = datetime(year, 1, 1)
            actual_date = base_date + timedelta(days=day_of_year - 1)
            
            return actual_date.strftime('%Y-%m-%d')
        except:
            return datetime.now().strftime('%Y-%m-%d')
    
    def get_satellite_positions(self, use_cache=True):
        """Get current positions of all satellites with smooth interpolation"""
        current_time = self.ts.now()
        positions = []
        
        for norad_id, sat_data in self.satellites.items():
            try:
                satellite = sat_data['satellite']
                
                # Calculate current position
                geocentric = satellite.at(current_time)
                subpoint = geocentric.subpoint()
                
                # Calculate velocity for smooth movement
                velocity_vector = self._calculate_velocity(satellite, current_time)
                
                # Check if category needs updating (geostationary detection)
                altitude = subpoint.elevation.km
                if altitude > 35000 and sat_data['category'] == 'Other':
                    sat_data['category'] = 'Geostationary'
                    sat_data['color'] = self.categories.get_category_info('Geostationary')['color']
                
                position_data = {
                    'norad_id': norad_id,
                    'name': sat_data['name'],
                    'latitude': subpoint.latitude.degrees,
                    'longitude': subpoint.longitude.degrees,
                    'altitude': altitude,
                    'velocity': velocity_vector['speed'],
                    'velocity_vector': velocity_vector,
                    'category': sat_data['category'],
                    'color': sat_data['color'],
                    'launch_date': sat_data['launch_date'],
                    'orbital_period': self._calculate_orbital_period(satellite)
                }
                
                # Cache position for smooth movement
                sat_data['last_position'] = position_data
                sat_data['last_update'] = datetime.now()
                
                positions.append(position_data)
                
            except Exception as e:
                logging.error(f"Error calculating position for satellite {norad_id}: {e}")
                continue
        
        return positions
    
    def _calculate_velocity(self, satellite, current_time):
        """Calculate velocity vector for smooth movement"""
        try:
            # Calculate position at current time and 1 second later
            time_delta = self.ts.ut1_jd(current_time.ut1 + 1/86400)
            
            current_pos = satellite.at(current_time)
            future_pos = satellite.at(time_delta)
            
            current_subpoint = current_pos.subpoint()
            future_subpoint = future_pos.subpoint()
            
            # Calculate velocity components
            lat_diff = future_subpoint.latitude.degrees - current_subpoint.latitude.degrees
            lon_diff = future_subpoint.longitude.degrees - current_subpoint.longitude.degrees
            alt_diff = future_subpoint.elevation.km - current_subpoint.elevation.km
            
            # Calculate ground speed (approximate)
            ground_speed = np.sqrt(lat_diff**2 + lon_diff**2) * 111000  # m/s
            
            return {
                'speed': ground_speed * 3.6,  # km/h
                'lat_velocity': lat_diff * 3600,  # degrees per hour
                'lon_velocity': lon_diff * 3600,  # degrees per hour
                'alt_velocity': alt_diff * 3600   # km per hour
            }
        except:
            return {'speed': 0, 'lat_velocity': 0, 'lon_velocity': 0, 'alt_velocity': 0}
    
    def _calculate_orbital_period(self, satellite):
        """Calculate orbital period in minutes"""
        try:
            line2 = satellite.model.line2
            mean_motion = float(line2[52:63])
            return 1440.0 / mean_motion  # minutes per revolution
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
                'inclination': satellite.model.inclo * 180 / np.pi,
                'eccentricity': satellite.model.ecco,
                'color': sat_data['color']
            }
        except Exception as e:
            logging.error(f"Error getting details for satellite {norad_id}: {e}")
            return None
    
    def get_satellite_orbit_path(self, norad_id, duration_hours=3):
        """Get orbit path for a satellite"""
        if norad_id not in self.satellites:
            return []
        
        satellite = self.satellites[norad_id]['satellite']
        current_time = self.ts.now()
        
        orbit_points = []
        minutes = duration_hours * 60
        
        for i in range(0, minutes, 3):  # Every 3 minutes for smoother orbits
            try:
                t = self.ts.ut1_jd(current_time.ut1 + i / (24 * 60))
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
        
        for i in range(0, minutes, 1):  # Every minute for smooth ground tracks
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