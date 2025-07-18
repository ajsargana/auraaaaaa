import requests
import numpy as np
from datetime import datetime, timedelta
from skyfield.api import load, EarthSatellite
from skyfield.timelib import Time
import logging
import time
import re

class SatelliteTracker:
    def __init__(self):
        self.ts = load.timescale()
        self.satellites = {}
        self.categories = self._define_categories()
        self.last_update = None
        self.update_interval = 86400  # 1 day in seconds (24 hours)
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
                'color': '#FFEAA7',
                'satellites': []
            },
            'Space_Telescopes': {
                'name': 'Space Telescopes',
                'color': '#264653',
                'satellites': []
            },
            'Military': {
                'name': 'Military Satellites',
                'color': '#DDA0DD',
                'satellites': []
            },
            'CubeSats': {
                'name': 'CubeSats',
                'color': '#F72585',
                'satellites': []
            },
            'Amateur_Radio': {
                'name': 'Amateur Radio',
                'color': '#4CC9F0',
                'satellites': []
            },
            'Technology_Demo': {
                'name': 'Technology Demo',
                'color': '#7209B7',
                'satellites': []
            },
            'Debris_Tracking': {
                'name': 'Debris & Tracking',
                'color': '#A44A3F',
                'satellites': []
            },
            'Geostationary': {
                'name': 'Geostationary Orbit',
                'color': '#F77F00',
                'satellites': []
            },
            'LEO_Constellation': {
                'name': 'LEO Constellations',
                'color': '#FCBF49',
                'satellites': []
            },
            'Commercial': {
                'name': 'Commercial Satellites',
                'color': '#FFB347',
                'satellites': []
            },
            'Rocket_Bodies': {
                'name': 'Rocket Bodies',
                'color': '#8B5A3C',
                'satellites': []
            },
            'Other': {
                'name': 'Other Satellites',
                'color': '#A8A8A8',
                'satellites': []
            }
        }
    
    def load_tle_data(self):
        """Load TLE data from multiple sources with fallbacks"""
        try:
            logging.info("Loading TLE data from available sources...")
            
            # Primary and fallback TLE sources
            tle_source_sets = [
                # CelesTrak (primary) - comprehensive set
                [
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=galileo&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=glonass-ops&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=beidou&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=science&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-next&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=noaa&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=goes&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=cubesat&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=amateur&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=x-comm&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=geo&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=intelsat&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=ses&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=orbcomm&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=globalstar&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=military&FORMAT=tle',
                    'https://celestrak.org/NORAD/elements/gp.php?GROUP=radar&FORMAT=tle'
                ],
                # N2YO (fallback 1)
                [
                    'https://www.n2yo.com/tle/download.php?catalog=stations',
                    'https://www.n2yo.com/tle/download.php?catalog=weather',
                    'https://www.n2yo.com/tle/download.php?catalog=gps'
                ],
                # Space-Track.org alternative format (fallback 2)
                [
                    'https://celestrak.org/NORAD/elements/stations.txt',
                    'https://celestrak.org/NORAD/elements/weather.txt',
                    'https://celestrak.org/NORAD/elements/gps.txt'
                ]
            ]
            
            all_satellites = {}
            satellite_count = 0
            
            for source_index, tle_urls in enumerate(tle_source_sets):
                if satellite_count >= 2000:  # Increased limit for more satellites
                    break
                    
                logging.info(f"Trying TLE source set {source_index + 1}")
                successful_loads = 0
                
                for url in tle_urls:
                    if satellite_count >= 2000:
                        break
                        
                    try:
                        response = requests.get(url, timeout=15)
                        response.raise_for_status()
                        
                        lines = response.text.strip().split('\n')
                        url_satellite_count = 0
                        
                        # Parse TLE data
                        for i in range(0, len(lines) - 2, 3):
                            if satellite_count >= 2000 or url_satellite_count >= 2000:
                                break
                                
                            if i + 2 < len(lines):
                                name = lines[i].strip()
                                line1 = lines[i + 1].strip()
                                line2 = lines[i + 2].strip()
                                
                                # Validate TLE format
                                if (line1.startswith('1 ') and line2.startswith('2 ') and 
                                    len(line1) == 69 and len(line2) == 69):
                                    
                                    try:
                                        satellite = EarthSatellite(line1, line2, name, self.ts)
                                        norad_id = int(line1[2:7])
                                        
                                        if norad_id not in all_satellites:
                                            all_satellites[norad_id] = {
                                                'satellite': satellite,
                                                'name': name,
                                                'tle_line1': line1,
                                                'tle_line2': line2,
                                                'category': self._categorize_satellite(name, norad_id)
                                            }
                                            satellite_count += 1
                                            url_satellite_count += 1
                                            
                                    except Exception as e:
                                        logging.warning(f"Error creating satellite {name}: {e}")
                                        continue
                                        
                        if url_satellite_count > 0:
                            successful_loads += 1
                            logging.info(f"Loaded {url_satellite_count} satellites from {url}")
                            
                    except Exception as e:
                        logging.warning(f"Error fetching TLE data from {url}: {e}")
                        continue
                
                # If we got some satellites from this source set, we're good
                if successful_loads > 0:
                    logging.info(f"Successfully loaded from source set {source_index + 1}")
                    break
                else:
                    logging.warning(f"Failed to load from source set {source_index + 1}, trying next...")
            
            # If no source worked, use fallback data
            if not all_satellites:
                logging.error("All TLE sources failed, using fallback data")
                self._load_fallback_data()
                return
            
            self.satellites = all_satellites
            self.last_update = time.time()
            
            # Update category satellite lists
            self._update_category_lists()
            
            logging.info(f"Loaded {len(self.satellites)} satellites")
            
        except Exception as e:
            logging.error(f"Error loading TLE data: {e}")
            # Load fallback data if available
            if not self.satellites:
                self._load_fallback_data()
    
    def _categorize_satellite(self, name, norad_id):
        """Categorize satellite based on name and NORAD ID"""
        name_lower = name.lower()
        
        # ISS
        if norad_id == 25544 or 'iss' in name_lower:
            return 'ISS'
        
        # Navigation systems
        if 'gps' in name_lower or 'navstar' in name_lower:
            return 'GPS'
        if 'glonass' in name_lower:
            return 'GLONASS'
        if 'galileo' in name_lower:
            return 'Galileo'
        if 'beidou' in name_lower or 'compass' in name_lower:
            return 'BeiDou'
        
        # Constellations
        if 'starlink' in name_lower:
            return 'Starlink'
        if 'oneweb' in name_lower:
            return 'OneWeb'
        if 'iridium' in name_lower:
            return 'Iridium'
        
        # Weather and Earth observation
        if ('noaa' in name_lower or 'goes' in name_lower or 'meteosat' in name_lower or 
            'weather' in name_lower or 'metop' in name_lower or 'himawari' in name_lower):
            return 'Weather'
        if ('landsat' in name_lower or 'sentinel' in name_lower or 'terra' in name_lower or 
            'aqua' in name_lower or 'modis' in name_lower or 'worldview' in name_lower):
            return 'Earth_Observation'
        
        # Space telescopes and astronomy
        if ('hubble' in name_lower or 'kepler' in name_lower or 'tess' in name_lower or 
            'chandra' in name_lower or 'spitzer' in name_lower or 'jwst' in name_lower or
            'telescope' in name_lower or 'observatory' in name_lower):
            return 'Space_Telescopes'
        
        # Scientific satellites
        if ('science' in name_lower or 'research' in name_lower or 'explorer' in name_lower or
            'mission' in name_lower or 'experiment' in name_lower):
            return 'Scientific'
        
        # CubeSats and small satellites
        if ('cubesat' in name_lower or 'cube' in name_lower or 'picosatellite' in name_lower or
            'nanosat' in name_lower or 'microsat' in name_lower):
            return 'CubeSats'
        
        # Amateur radio
        if ('amateur' in name_lower or 'ham' in name_lower or 'radio' in name_lower and 'sat' in name_lower):
            return 'Amateur_Radio'
        
        # Technology demonstration
        if ('demo' in name_lower or 'test' in name_lower or 'technology' in name_lower or
            'experimental' in name_lower):
            return 'Technology_Demo'
        
        # Military satellites
        if ('usa' in name_lower or 'nro' in name_lower or 'dscs' in name_lower or 
            'milstar' in name_lower or 'sbirs' in name_lower or 'lacrosse' in name_lower):
            return 'Military'
        
        # Rocket bodies and debris
        if ('rocket' in name_lower or 'r/b' in name_lower or 'debris' in name_lower or
            'stage' in name_lower):
            return 'Rocket_Bodies'
        
        # Communication satellites
        if ('intelsat' in name_lower or 'eutelsat' in name_lower or 'ses' in name_lower or 
            'communication' in name_lower or 'telecom' in name_lower or 'broadcast' in name_lower):
            return 'Communication'
        
        # Check for geostationary orbit (altitude around 35,786 km)
        # We'll categorize based on name patterns for now
        if ('geo' in name_lower or 'geostationary' in name_lower):
            return 'Geostationary'
        
        return 'Other'
    
    def _update_category_lists(self):
        """Update satellite lists for each category"""
        for category in self.categories.values():
            category['satellites'] = []
        
        for norad_id, sat_data in self.satellites.items():
            category = sat_data['category']
            if category in self.categories:
                self.categories[category]['satellites'].append(norad_id)
    
    def _load_fallback_data(self):
        """Load minimal fallback data if TLE fetch fails"""
        logging.warning("Using fallback satellite data")
        # Create ISS entry as fallback
        iss_tle1 = "1 25544U 98067A   23001.00000000  .00002182  00000-0  40768-4 0  9990"
        iss_tle2 = "2 25544  51.6461 339.7939 0001220  92.8340 267.3124 15.49309239 00000"
        
        try:
            iss = EarthSatellite(iss_tle1, iss_tle2, "ISS (ZARYA)", self.ts)
            self.satellites = {
                25544: {
                    'satellite': iss,
                    'name': "ISS (ZARYA)",
                    'tle_line1': iss_tle1,
                    'tle_line2': iss_tle2,
                    'category': 'ISS'
                }
            }
            self._update_category_lists()
        except Exception as e:
            logging.error(f"Error creating fallback data: {e}")
    
    def get_current_time(self):
        """Get current time in ISO format"""
        return datetime.utcnow().isoformat() + 'Z'
    
    def get_satellite_positions(self):
        """Get current positions of all satellites"""
        if self._should_update_tle():
            self.load_tle_data()
        
        current_time = self.ts.now()
        satellites_data = []
        
        for norad_id, sat_data in self.satellites.items():
            try:
                satellite = sat_data['satellite']
                geocentric = satellite.at(current_time)
                subpoint = geocentric.subpoint()
                
                # Calculate velocity more accurately
                dt1 = self.ts.tt_jd(current_time.tt - 0.5/86400)  # 0.5 seconds before
                dt2 = self.ts.tt_jd(current_time.tt + 0.5/86400)  # 0.5 seconds after
                geocentric_before = satellite.at(dt1)
                geocentric_after = satellite.at(dt2)
                velocity_vector = geocentric_after.position.km - geocentric_before.position.km
                velocity = np.linalg.norm(velocity_vector) * 1000  # m/s (distance in 1 second)
                
                # Get orbital period from TLE
                mean_motion = float(sat_data['tle_line2'][52:63])
                orbital_period = 1440 / mean_motion if mean_motion > 0 else 0  # minutes
                
                # Extract launch date from TLE if available
                launch_date = None
                try:
                    # TLE epoch can give us approximate launch timeframe
                    tle_epoch = sat_data['tle_line1'][18:32]
                    # This is a rough approximation - in reality would need separate launch date database
                    year = int('20' + tle_epoch[:2]) if tle_epoch[:2] < '57' else int('19' + tle_epoch[:2])
                    day_of_year = float(tle_epoch[2:])
                    launch_date = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)
                    launch_date = launch_date.strftime("%Y-%m-%d")
                except:
                    launch_date = "Unknown"

                

                satellites_data.append({
                    'norad_id': norad_id,
                    'name': sat_data['name'],
                    'latitude': subpoint.latitude.degrees,
                    'longitude': subpoint.longitude.degrees,
                    'altitude': subpoint.elevation.km,
                    'velocity': velocity,
                    'orbital_period': orbital_period,
                    'category': sat_data['category'],
                    'color': self.categories[sat_data['category']]['color'],
                    'launch_date': launch_date
                })
                
            except Exception as e:
                logging.warning(f"Error calculating position for satellite {norad_id}: {e}")
                continue
        
        return satellites_data
    
    def get_satellite_details(self, norad_id):
        """Get detailed information for a specific satellite"""
        if norad_id not in self.satellites:
            return None
        
        sat_data = self.satellites[norad_id]
        satellite = sat_data['satellite']
        current_time = self.ts.now()
        
        try:
            geocentric = satellite.at(current_time)
            subpoint = geocentric.subpoint()
            
            # Calculate velocity
            dt1 = self.ts.tt_jd(current_time.tt - 0.5/86400)  # 0.5 seconds before
            dt2 = self.ts.tt_jd(current_time.tt + 0.5/86400)  # 0.5 seconds after
            geocentric_before = satellite.at(dt1)
            geocentric_after = satellite.at(dt2)
            velocity_vector = geocentric_after.position.km - geocentric_before.position.km
            velocity = np.linalg.norm(velocity_vector) * 1000  # m/s (distance in 1 second)
            
            # Parse TLE for additional orbital elements
            tle_line1 = sat_data['tle_line1']
            tle_line2 = sat_data['tle_line2']
            
            inclination = float(tle_line2[8:16])
            eccentricity = float('0.' + tle_line2[26:33])
            arg_perigee = float(tle_line2[34:42])
            mean_anomaly = float(tle_line2[43:51])
            mean_motion = float(tle_line2[52:63])
            
            orbital_period = 1440 / mean_motion if mean_motion > 0 else 0
            
            # Determine orbit type based on altitude
            altitude_km = subpoint.elevation.km
            if altitude_km < 2000:
                orbit_type = "LEO (Low Earth Orbit)"
            elif altitude_km < 35000:
                orbit_type = "MEO (Medium Earth Orbit)"
            else:
                orbit_type = "GEO (Geostationary Orbit)"
            
            # Determine country/agency from name patterns
            country = self._get_country_from_satellite(sat_data['name'], norad_id)
            agency = self._get_agency_from_satellite(sat_data['name'], sat_data['category'])
            satellite_type = self._get_satellite_type(sat_data['category'])
            
            # Extract launch date from TLE epoch
            launch_date = self._extract_launch_date(tle_line1[18:32])
            
            # Determine visibility
            visibility = "Visible" if altitude_km < 1000 else "Telescope Required"
            
            # Determine status
            status = "Active" if mean_motion > 0 else "Inactive"
            
            return {
                'norad_id': norad_id,
                'name': sat_data['name'],
                'category': sat_data['category'],
                'orbit': {
                    'altitude': altitude_km,
                    'inclination': inclination,
                    'period': orbital_period,
                    'velocity': velocity / 1000,  # km/s
                    'orbit_type': orbit_type
                },
                'position': {
                    'latitude': subpoint.latitude.degrees,
                    'longitude': subpoint.longitude.degrees,
                    'country': country,
                    'visibility': visibility
                },
                'technical': {
                    'norad_id': norad_id,
                    'launch_date': launch_date,
                    'type': satellite_type,
                    'agency': agency,
                    'status': status
                },
                'tle_data': {
                    'line1': tle_line1,
                    'line2': tle_line2,
                    'epoch': tle_line1[18:32]
                }
            }
            
        except Exception as e:
            logging.error(f"Error getting satellite details: {e}")
            return None
    
    def _get_country_from_satellite(self, name, norad_id):
        """Determine country based on satellite name and NORAD ID"""
        name_lower = name.lower()
        
        # ISS is international
        if norad_id == 25544:
            return "International"
        
        # USA patterns
        if any(pattern in name_lower for pattern in ['usa', 'noaa', 'goes', 'landsat', 'aqua', 'terra']):
            return "United States"
        
        # Russia patterns
        if any(pattern in name_lower for pattern in ['cosmos', 'glonass', 'meteor', 'resurs']):
            return "Russia"
        
        # China patterns
        if any(pattern in name_lower for pattern in ['beidou', 'fengyun', 'yaogan', 'tiangong']):
            return "China"
        
        # Europe patterns
        if any(pattern in name_lower for pattern in ['galileo', 'sentinel', 'meteosat', 'eutelsat']):
            return "Europe (ESA)"
        
        # Japan patterns
        if any(pattern in name_lower for pattern in ['himawari', 'jaxa', 'mtsat']):
            return "Japan"
        
        # India patterns
        if any(pattern in name_lower for pattern in ['insat', 'cartosat', 'resourcesat']):
            return "India"
        
        # Commercial/Private
        if any(pattern in name_lower for pattern in ['starlink', 'oneweb', 'iridium']):
            return "Commercial"
        
        return "Unknown"
    
    def _get_agency_from_satellite(self, name, category):
        """Determine agency based on satellite name and category"""
        name_lower = name.lower()
        
        if 'starlink' in name_lower:
            return "SpaceX"
        elif 'oneweb' in name_lower:
            return "OneWeb"
        elif 'iridium' in name_lower:
            return "Iridium Communications"
        elif any(pattern in name_lower for pattern in ['noaa', 'goes', 'landsat']):
            return "NASA/NOAA"
        elif 'glonass' in name_lower:
            return "Roscosmos"
        elif 'galileo' in name_lower:
            return "ESA"
        elif 'beidou' in name_lower:
            return "CNSA"
        elif category == 'ISS':
            return "NASA/Roscosmos/ESA/JAXA"
        elif category == 'Military':
            return "Defense Department"
        else:
            return "Various"
    
    def _get_satellite_type(self, category):
        """Get satellite type based on category"""
        type_mapping = {
            'ISS': 'Space Station',
            'GPS': 'Navigation',
            'GLONASS': 'Navigation',
            'Galileo': 'Navigation',
            'BeiDou': 'Navigation',
            'Weather': 'Weather/Climate',
            'Earth_Observation': 'Earth Observation',
            'Communication': 'Communication',
            'Starlink': 'Internet Constellation',
            'OneWeb': 'Internet Constellation',
            'Iridium': 'Communication',
            'Scientific': 'Scientific Research',
            'Space_Telescopes': 'Space Observatory',
            'Military': 'Defense/Intelligence',
            'CubeSats': 'Small Satellite',
            'Amateur_Radio': 'Amateur Radio',
            'Technology_Demo': 'Technology Demo',
            'Debris_Tracking': 'Debris/Inactive',
            'Geostationary': 'Communication/Broadcasting',
            'LEO_Constellation': 'Constellation',
            'Commercial': 'Commercial',
            'Rocket_Bodies': 'Rocket Stage/Debris'
        }
        return type_mapping.get(category, 'Unknown')
    
    def _extract_launch_date(self, epoch_str):
        """Extract approximate launch date from TLE epoch"""
        try:
            year = int('20' + epoch_str[:2]) if epoch_str[:2] < '57' else int('19' + epoch_str[:2])
            day_of_year = float(epoch_str[2:])
            launch_date = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)
            return launch_date.strftime("%Y-%m-%d")
        except:
            return "Unknown"
    
    def get_orbital_path(self, norad_id, hours=2):
        """Get orbital path points for visualization"""
        if norad_id not in self.satellites:
            return []
        
        satellite = self.satellites[norad_id]['satellite']
        current_time = self.ts.now()
        
        # Generate points for the next few hours
        time_points = []
        num_points = 100
        
        for i in range(num_points):
            dt = current_time.tt + (i * hours) / (24 * num_points)
            time_points.append(self.ts.tt_jd(dt))
        
        orbit_points = []
        
        for t in time_points:
            try:
                geocentric = satellite.at(t)
                subpoint = geocentric.subpoint()
                
                orbit_points.append({
                    'latitude': subpoint.latitude.degrees,
                    'longitude': subpoint.longitude.degrees,
                    'altitude': subpoint.elevation.km
                })
                
            except Exception as e:
                logging.warning(f"Error calculating orbit point: {e}")
                continue
        
        return orbit_points
    
    def get_next_passes(self, norad_id, observer_lat, observer_lon, observer_alt=0, days=7):
        """Calculate next passes of satellite over observer location"""
        if norad_id not in self.satellites:
            return []
        
        from skyfield.api import wgs84
        
        satellite = self.satellites[norad_id]['satellite']
        observer = wgs84.latlon(observer_lat, observer_lon, elevation_m=observer_alt)
        
        current_time = self.ts.now()
        end_time = self.ts.tt_jd(current_time.tt + days)
        
        passes = []
        
        try:
            # Find passes using skyfield's find_events
            t, events = satellite.find_events(observer, current_time, end_time, altitude_degrees=10.0)
            
            current_pass = {}
            
            for time_point, event in zip(t, events):
                if event == 0:  # Rise
                    current_pass = {
                        'rise_time': time_point.utc_iso(),
                        'rise_azimuth': None
                    }
                elif event == 1:  # Culmination (highest point)
                    if current_pass:
                        topocentric = (satellite - observer).at(time_point)
                        alt, az, distance = topocentric.altaz()
                        current_pass.update({
                            'culmination_time': time_point.utc_iso(),
                            'max_elevation': alt.degrees,
                            'culmination_azimuth': az.degrees
                        })
                elif event == 2:  # Set
                    if current_pass:
                        current_pass['set_time'] = time_point.utc_iso()
                        
                        # Calculate rise and set azimuths
                        if 'rise_time' in current_pass:
                            rise_t = self.ts.from_datetime(datetime.fromisoformat(current_pass['rise_time'].replace('Z', '+00:00')))
                            topocentric_rise = (satellite - observer).at(rise_t)
                            _, az_rise, _ = topocentric_rise.altaz()
                            current_pass['rise_azimuth'] = az_rise.degrees
                        
                        topocentric_set = (satellite - observer).at(time_point)
                        _, az_set, _ = topocentric_set.altaz()
                        current_pass['set_azimuth'] = az_set.degrees
                        
                        # Calculate duration
                        if 'rise_time' in current_pass:
                            rise_dt = datetime.fromisoformat(current_pass['rise_time'].replace('Z', '+00:00'))
                            set_dt = datetime.fromisoformat(current_pass['set_time'].replace('Z', '+00:00'))
                            duration = (set_dt - rise_dt).total_seconds() / 60  # minutes
                            current_pass['duration_minutes'] = duration
                        
                        passes.append(current_pass)
                        current_pass = {}
                        
        except Exception as e:
            logging.error(f"Error calculating passes: {e}")
        
        return passes[:3]  # Return next 3 passes
    
    def get_satellite_categories(self):
        """Get satellite categories with counts"""
        categories_with_counts = {}
        
        for cat_name, cat_data in self.categories.items():
            categories_with_counts[cat_name] = {
                'name': cat_data['name'],
                'color': cat_data['color'],
                'count': len(cat_data['satellites']),
                'satellites': cat_data['satellites']
            }
        
        return categories_with_counts
    
    def refresh_tle_data(self):
        """Force refresh of TLE data"""
        self.load_tle_data()
    
    def _should_update_tle(self):
        """Check if TLE data should be updated"""
        if self.last_update is None:
            return True
        return time.time() - self.last_update > self.update_interval
