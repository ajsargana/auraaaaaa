
"""
Airplane Data Manager - Handles real-time airplane tracking and data management
Separated from satellite functionality for better organization
"""
import os
import logging
import requests
from datetime import datetime, timezone
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirplaneDataManager:
    def __init__(self):
        self.airplanes = {}
        self.last_update = None
        self.opensky_api_url = "https://opensky-network.org/api/states/all"
        self.cache_duration = 30  # Cache data for 30 seconds
        self.last_api_call = None
        
    def load_airplane_data(self, force_refresh=False):
        """Get current airplane positions from OpenSky API with caching"""
        try:
            # Check if we have recent cached data
            now = datetime.now(timezone.utc)
            if (not force_refresh and self.last_api_call and 
                (now - self.last_api_call).total_seconds() < self.cache_duration):
                logger.info(f"Using cached airplane data from {self.cache_duration}s ago")
                return True

            logger.info("Fetching airplane data from OpenSky Network...")
            self.last_api_call = now
            
            response = requests.get(self.opensky_api_url, timeout=15)  # Increased timeout
            if not response.ok:
                raise Exception(f"OpenSky API error: {response.status_code}")

            data = response.json()

            if not data or 'states' not in data:
                logger.warning("No airplane data available from OpenSky")
                return False

            airplanes = {}
            valid_count = 0
            filtered_count = 0

            for state in data['states']:
                if state and len(state) >= 17:
                    # OpenSky state vector format:
                    # [0: icao24, 1: callsign, 2: origin_country, 3: time_position, 4: last_contact,
                    #  5: longitude, 6: latitude, 7: baro_altitude, 8: on_ground, 9: velocity,
                    #  10: true_track, 11: vertical_rate, 12: sensors, 13: geo_altitude, 
                    #  14: squawk, 15: spi, 16: position_source]

                    lat = state[6]
                    lon = state[5]
                    alt = state[7]  # barometric altitude in meters
                    callsign = state[1]
                    icao24 = state[0]

                    # Skip if no position data or invalid coordinates
                    if (lat is None or lon is None or 
                        not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)) or
                        abs(lat) > 90 or abs(lon) > 180):
                        continue

                    # Skip if ICAO24 is invalid
                    if not icao24 or len(icao24) != 6:
                        continue

                    valid_count += 1

                    # Better altitude handling
                    altitude_meters = alt if alt is not None and alt >= 0 else 0
                    geo_alt_meters = state[13] if state[13] is not None and state[13] >= 0 else altitude_meters

                    # Use geo altitude if barometric is missing or unrealistic
                    if altitude_meters == 0 and geo_alt_meters > 0:
                        altitude_meters = geo_alt_meters
                    elif altitude_meters > 50000:  # Unrealistic commercial altitude
                        altitude_meters = geo_alt_meters if geo_alt_meters < 50000 else 10000

                    # Better callsign processing
                    processed_callsign = ''
                    if callsign and isinstance(callsign, str):
                        processed_callsign = callsign.strip()
                        # Remove null characters and invalid characters
                        processed_callsign = ''.join(c for c in processed_callsign if c.isprintable())

                    # Better country handling
                    country = state[2] if state[2] and isinstance(state[2], str) else 'Unknown'

                    # Velocity validation
                    velocity = state[9] if state[9] is not None and state[9] >= 0 else 0
                    if velocity > 1000:  # Unrealistic velocity (>1000 m/s = >3600 km/h)
                        velocity = 0

                    # Track validation
                    true_track = state[10] if state[10] is not None and 0 <= state[10] <= 360 else 0

                    # Vertical rate validation
                    vertical_rate = state[11] if state[11] is not None and abs(state[11]) < 100 else 0

                    # Squawk code processing
                    squawk = str(state[14]) if state[14] is not None else ''

                    airplane = {
                        'icao24': icao24.lower(),
                        'callsign': processed_callsign,
                        'origin_country': country,
                        'latitude': round(lat, 6),
                        'longitude': round(lon, 6),
                        'altitude': round(altitude_meters / 1000.0, 3),  # km for consistency
                        'altitude_meters': int(altitude_meters),
                        'geo_altitude': round(geo_alt_meters / 1000.0, 3) if geo_alt_meters else 0,
                        'on_ground': bool(state[8]),
                        'velocity': round(velocity, 1),  # m/s
                        'true_track': round(true_track, 1),  # degrees
                        'heading': round(true_track, 1),  # alias for compatibility
                        'vertical_rate': round(vertical_rate, 2),  # m/s
                        'squawk': squawk,
                        'time_position': state[3],
                        'last_contact': state[4],
                        'position_source': state[16] if len(state) > 16 else 0,
                        'sensors': state[12] if len(state) > 12 else None,
                        'color': '#808080' if state[8] else '#FFD700',  # Gray for ground, gold for flying
                        'type': 'airplane'
                    }

                    # Filter out obviously invalid data
                    if (altitude_meters < 0 or altitude_meters > 50000 or
                        velocity < 0 or velocity > 500):  # Reasonable limits
                        filtered_count += 1
                        continue

                    airplanes[icao24] = airplane

            logger.info(f"OpenSky processing: {valid_count} valid, {filtered_count} filtered, {len(airplanes)} final airplanes")
            
            self.airplanes = airplanes
            self.last_update = datetime.now(timezone.utc)
            return True

        except Exception as e:
            logger.error(f"Error loading airplane data: {e}")
            return False

    def get_airplane_data(self):
        """Return all airplane data"""
        return list(self.airplanes.values())

    def get_airplane_by_icao24(self, icao24):
        """Get specific airplane by ICAO24 identifier"""
        return self.airplanes.get(icao24.lower())

    def search_airplanes(self, query):
        """Search airplanes by callsign, ICAO24, or country"""
        query_lower = query.lower()
        results = []
        
        for airplane in self.airplanes.values():
            if (query_lower in airplane['callsign'].lower() or
                query_lower in airplane['icao24'].lower() or
                query_lower in airplane['origin_country'].lower()):
                results.append(airplane)
                
        return results[:50]  # Limit to 50 results

    def get_airplane_details(self, icao24):
        """Get detailed information for a specific airplane"""
        airplane = self.get_airplane_by_icao24(icao24)
        if not airplane:
            return None

        # Calculate additional details
        lat = airplane['latitude']
        lon = airplane['longitude']
        alt_m = airplane['altitude_meters']
        velocity_ms = airplane['velocity']

        # Convert velocity from m/s to different units
        velocity_kmh = velocity_ms * 3.6
        velocity_knots = velocity_ms * 1.94384

        airplane_details = {
            'aircraft': {
                'icao24': airplane['icao24'],
                'callsign': airplane['callsign'] or 'Unknown',
                'origin_country': airplane['origin_country'],
                'squawk': airplane['squawk'] or 'N/A'
            },
            'position': {
                'latitude': lat,
                'longitude': lon,
                'altitude_meters': alt_m,
                'altitude_feet': alt_m * 3.28084 if alt_m else 0,
                'altitude_km': alt_m / 1000.0 if alt_m else 0,
                'on_ground': airplane['on_ground']
            },
            'flight': {
                'velocity_ms': velocity_ms,
                'velocity_kmh': velocity_kmh,
                'velocity_knots': velocity_knots,
                'true_track': airplane['true_track'],
                'vertical_rate_ms': airplane['vertical_rate'],
                'vertical_rate_fpm': (airplane['vertical_rate'] * 196.85) if airplane['vertical_rate'] else 0  # feet per minute
            },
            'technical': {
                'last_contact': airplane['last_contact'],
                'time_position': airplane['time_position'],
                'position_source': airplane['position_source'],
                'geo_altitude': airplane['geo_altitude'],
                'sensors': airplane['sensors']
            }
        }

        return airplane_details

    def refresh_data(self):
        """Refresh airplane data"""
        logger.info("Refreshing airplane data...")
        return self.load_airplane_data()

    def get_status(self):
        """Get airplane tracking status"""
        return {
            'airplanes_loaded': len(self.airplanes),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'data_source': 'OpenSky Network'
        }

    def get_airplane_count(self):
        """Get total airplane count"""
        return len(self.airplanes)

    def clear_airplane_data(self):
        """Clear all airplane data"""
        self.airplanes.clear()
        self.last_update = None
