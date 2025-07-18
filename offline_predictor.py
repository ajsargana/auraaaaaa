
import os
import logging
import numpy as np
from datetime import datetime, timedelta
from skyfield.api import load, EarthSatellite
from skyfield.timelib import Time
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import json
import time

class OfflineSatellitePredictor:
    def __init__(self):
        self.ts = load.timescale()
        self.connection_pool = None
        self.satellites_cache = {}
        self.orbital_elements_cache = {}
        self._init_db_connection()
        self._ensure_tables()
        
    def _init_db_connection(self):
        """Initialize PostgreSQL connection pool"""
        try:
            database_url = os.environ.get("DATABASE_URL")
            if database_url:
                # Use Neon's connection pooler for better performance
                database_url = database_url.replace('.us-east-2', '-pooler.us-east-2')
                self.connection_pool = pool.SimpleConnectionPool(
                    1, 10, database_url
                )
                logging.info("Offline predictor database connection established")
            else:
                logging.warning("No DATABASE_URL found, offline prediction will be limited")
        except Exception as e:
            logging.error(f"Failed to initialize database connection: {e}")
    
    def _ensure_tables(self):
        """Create necessary tables for offline prediction"""
        if not self.connection_pool:
            return
            
        conn = None
        try:
            conn = self.connection_pool.getconn()
            cur = conn.cursor()
            
            # TLE cache table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tle_cache (
                    norad_id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    tle_line1 VARCHAR(69) NOT NULL,
                    tle_line2 VARCHAR(69) NOT NULL,
                    category VARCHAR(50),
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Orbital elements cache table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orbital_elements_cache (
                    norad_id INTEGER PRIMARY KEY,
                    semi_major_axis FLOAT,
                    eccentricity FLOAT,
                    inclination FLOAT,
                    raan FLOAT,
                    arg_perigee FLOAT,
                    mean_anomaly FLOAT,
                    mean_motion FLOAT,
                    epoch_year INTEGER,
                    epoch_day FLOAT,
                    bstar FLOAT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (norad_id) REFERENCES tle_cache(norad_id)
                );
            """)
            
            # Index for faster queries
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tle_updated ON tle_cache(last_updated);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_orbital_updated ON orbital_elements_cache(last_updated);")
            
            conn.commit()
            logging.info("Offline prediction tables created/verified")
            
        except Exception as e:
            logging.error(f"Error creating tables: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                cur.close()
                self.connection_pool.putconn(conn)
    
    def cache_tle_data(self, satellites_data):
        """Cache TLE data and compute orbital elements for offline use"""
        if not self.connection_pool:
            logging.warning("No database connection, cannot cache TLE data")
            return
            
        conn = None
        try:
            conn = self.connection_pool.getconn()
            cur = conn.cursor()
            
            cached_count = 0
            
            for norad_id, sat_data in satellites_data.items():
                try:
                    # Cache TLE data
                    cur.execute("""
                        INSERT INTO tle_cache (norad_id, name, tle_line1, tle_line2, category, last_updated)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (norad_id) 
                        DO UPDATE SET 
                            name = EXCLUDED.name,
                            tle_line1 = EXCLUDED.tle_line1,
                            tle_line2 = EXCLUDED.tle_line2,
                            category = EXCLUDED.category,
                            last_updated = EXCLUDED.last_updated;
                    """, (
                        norad_id,
                        sat_data['name'],
                        sat_data['tle_line1'],
                        sat_data['tle_line2'],
                        sat_data['category'],
                        datetime.now()
                    ))
                    
                    # Extract and cache orbital elements
                    orbital_elements = self._extract_orbital_elements(
                        sat_data['tle_line1'], 
                        sat_data['tle_line2']
                    )
                    
                    if orbital_elements:
                        cur.execute("""
                            INSERT INTO orbital_elements_cache (
                                norad_id, semi_major_axis, eccentricity, inclination,
                                raan, arg_perigee, mean_anomaly, mean_motion,
                                epoch_year, epoch_day, bstar, last_updated
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (norad_id)
                            DO UPDATE SET
                                semi_major_axis = EXCLUDED.semi_major_axis,
                                eccentricity = EXCLUDED.eccentricity,
                                inclination = EXCLUDED.inclination,
                                raan = EXCLUDED.raan,
                                arg_perigee = EXCLUDED.arg_perigee,
                                mean_anomaly = EXCLUDED.mean_anomaly,
                                mean_motion = EXCLUDED.mean_motion,
                                epoch_year = EXCLUDED.epoch_year,
                                epoch_day = EXCLUDED.epoch_day,
                                bstar = EXCLUDED.bstar,
                                last_updated = EXCLUDED.last_updated;
                        """, (
                            norad_id,
                            orbital_elements['semi_major_axis'],
                            orbital_elements['eccentricity'],
                            orbital_elements['inclination'],
                            orbital_elements['raan'],
                            orbital_elements['arg_perigee'],
                            orbital_elements['mean_anomaly'],
                            orbital_elements['mean_motion'],
                            orbital_elements['epoch_year'],
                            orbital_elements['epoch_day'],
                            orbital_elements['bstar'],
                            datetime.now()
                        ))
                    
                    cached_count += 1
                    
                except Exception as e:
                    logging.warning(f"Error caching satellite {norad_id}: {e}")
                    continue
            
            conn.commit()
            logging.info(f"Cached {cached_count} satellites for offline prediction")
            
        except Exception as e:
            logging.error(f"Error caching TLE data: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                cur.close()
                self.connection_pool.putconn(conn)
    
    def _extract_orbital_elements(self, tle_line1, tle_line2):
        """Extract orbital elements from TLE for faster calculations"""
        try:
            # Parse TLE lines for orbital elements
            inclination = float(tle_line2[8:16])
            raan = float(tle_line2[17:25])  # Right Ascension of Ascending Node
            eccentricity = float('0.' + tle_line2[26:33])
            arg_perigee = float(tle_line2[34:42])
            mean_anomaly = float(tle_line2[43:51])
            mean_motion = float(tle_line2[52:63])  # revolutions per day
            
            # Extract epoch information
            epoch_year = int('20' + tle_line1[18:20]) if tle_line1[18:20] < '57' else int('19' + tle_line1[18:20])
            epoch_day = float(tle_line1[20:32])
            
            # Extract BSTAR drag coefficient
            bstar_str = tle_line1[53:61]
            bstar_sign = 1 if bstar_str[0] != '-' else -1
            bstar_mantissa = float(bstar_str[1:6]) if bstar_str[1:6].strip() else 0
            bstar_exponent = int(bstar_str[6:8]) if bstar_str[6:8].strip() else 0
            bstar = bstar_sign * bstar_mantissa * (10 ** (bstar_exponent - 5))
            
            # Calculate semi-major axis from mean motion
            # Using Kepler's third law: n² = μ/a³
            mu = 398600.4418  # Earth's gravitational parameter (km³/s²)
            n = mean_motion * 2 * np.pi / 86400  # Convert rev/day to rad/s
            semi_major_axis = (mu / (n ** 2)) ** (1/3)
            
            return {
                'semi_major_axis': semi_major_axis,
                'eccentricity': eccentricity,
                'inclination': inclination,
                'raan': raan,
                'arg_perigee': arg_perigee,
                'mean_anomaly': mean_anomaly,
                'mean_motion': mean_motion,
                'epoch_year': epoch_year,
                'epoch_day': epoch_day,
                'bstar': bstar
            }
            
        except Exception as e:
            logging.error(f"Error extracting orbital elements: {e}")
            return None
    
    def load_cached_satellites(self):
        """Load satellites from cache for offline operation"""
        if not self.connection_pool:
            return {}
            
        conn = None
        try:
            conn = self.connection_pool.getconn()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Load TLE data with orbital elements
            cur.execute("""
                SELECT t.*, o.semi_major_axis, o.eccentricity, o.inclination,
                       o.raan, o.arg_perigee, o.mean_anomaly, o.mean_motion,
                       o.epoch_year, o.epoch_day, o.bstar
                FROM tle_cache t
                LEFT JOIN orbital_elements_cache o ON t.norad_id = o.norad_id
                ORDER BY t.last_updated DESC;
            """)
            
            results = cur.fetchall()
            cached_satellites = {}
            
            for row in results:
                try:
                    # Create EarthSatellite object
                    satellite = EarthSatellite(
                        row['tle_line1'], 
                        row['tle_line2'], 
                        row['name'], 
                        self.ts
                    )
                    
                    cached_satellites[row['norad_id']] = {
                        'satellite': satellite,
                        'name': row['name'],
                        'tle_line1': row['tle_line1'],
                        'tle_line2': row['tle_line2'],
                        'category': row['category'],
                        'orbital_elements': {
                            'semi_major_axis': row['semi_major_axis'],
                            'eccentricity': row['eccentricity'],
                            'inclination': row['inclination'],
                            'raan': row['raan'],
                            'arg_perigee': row['arg_perigee'],
                            'mean_anomaly': row['mean_anomaly'],
                            'mean_motion': row['mean_motion'],
                            'epoch_year': row['epoch_year'],
                            'epoch_day': row['epoch_day'],
                            'bstar': row['bstar']
                        } if row['semi_major_axis'] else None,
                        'last_updated': row['last_updated']
                    }
                    
                except Exception as e:
                    logging.warning(f"Error loading cached satellite {row['norad_id']}: {e}")
                    continue
            
            logging.info(f"Loaded {len(cached_satellites)} satellites from cache")
            return cached_satellites
            
        except Exception as e:
            logging.error(f"Error loading cached satellites: {e}")
            return {}
        finally:
            if conn:
                cur.close()
                self.connection_pool.putconn(conn)
    
    def predict_position_offline(self, norad_id, current_time=None):
        """Predict satellite position using cached orbital elements (offline)"""
        if norad_id not in self.satellites_cache:
            # Try to load from database
            cached_sats = self.load_cached_satellites()
            self.satellites_cache.update(cached_sats)
        
        if norad_id not in self.satellites_cache:
            return None
        
        sat_data = self.satellites_cache[norad_id]
        
        try:
            if current_time is None:
                current_time = self.ts.now()
            
            # Use Skyfield's SGP4 propagation with cached satellite
            satellite = sat_data['satellite']
            geocentric = satellite.at(current_time)
            subpoint = geocentric.subpoint()
            
            # Calculate velocity efficiently
            dt = 0.5 / 86400  # 0.5 seconds in days
            t1 = self.ts.tt_jd(current_time.tt - dt)
            t2 = self.ts.tt_jd(current_time.tt + dt)
            
            pos1 = satellite.at(t1).position.km
            pos2 = satellite.at(t2).position.km
            velocity = np.linalg.norm(pos2 - pos1) * 1000  # m/s
            
            return {
                'norad_id': norad_id,
                'name': sat_data['name'],
                'latitude': subpoint.latitude.degrees,
                'longitude': subpoint.longitude.degrees,
                'altitude': subpoint.elevation.km,
                'velocity': velocity,
                'category': sat_data['category'],
                'offline_prediction': True,
                'last_tle_update': sat_data['last_updated'].isoformat() if sat_data['last_updated'] else None
            }
            
        except Exception as e:
            logging.error(f"Error predicting position for satellite {norad_id}: {e}")
            return None
    
    def predict_all_positions_offline(self, satellite_ids=None, current_time=None):
        """Predict positions for all or specified satellites offline"""
        if not self.satellites_cache:
            self.satellites_cache = self.load_cached_satellites()
        
        if current_time is None:
            current_time = self.ts.now()
        
        positions = []
        target_satellites = satellite_ids if satellite_ids else list(self.satellites_cache.keys())
        
        for norad_id in target_satellites:
            position = self.predict_position_offline(norad_id, current_time)
            if position:
                positions.append(position)
        
        return positions
    
    def is_cache_valid(self, max_age_hours=24):
        """Check if cached data is still valid"""
        if not self.connection_pool:
            return False
            
        conn = None
        try:
            conn = self.connection_pool.getconn()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT COUNT(*) as count, MAX(last_updated) as latest_update
                FROM tle_cache
                WHERE last_updated > %s;
            """, (datetime.now() - timedelta(hours=max_age_hours),))
            
            result = cur.fetchone()
            return result[0] > 0 if result else False
            
        except Exception as e:
            logging.error(f"Error checking cache validity: {e}")
            return False
        finally:
            if conn:
                cur.close()
                self.connection_pool.putconn(conn)
    
    def get_cache_stats(self):
        """Get statistics about cached data"""
        if not self.connection_pool:
            return None
            
        conn = None
        try:
            conn = self.connection_pool.getconn()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT 
                    COUNT(*) as total_satellites,
                    COUNT(o.norad_id) as satellites_with_elements,
                    MIN(t.last_updated) as oldest_update,
                    MAX(t.last_updated) as latest_update,
                    AVG(EXTRACT(EPOCH FROM (NOW() - t.last_updated))/3600) as avg_age_hours
                FROM tle_cache t
                LEFT JOIN orbital_elements_cache o ON t.norad_id = o.norad_id;
            """)
            
            return dict(cur.fetchone())
            
        except Exception as e:
            logging.error(f"Error getting cache stats: {e}")
            return None
        finally:
            if conn:
                cur.close()
                self.connection_pool.putconn(conn)
    
    def cleanup_old_cache(self, max_age_days=7):
        """Remove old cached data"""
        if not self.connection_pool:
            return
            
        conn = None
        try:
            conn = self.connection_pool.getconn()
            cur = conn.cursor()
            
            # Delete old orbital elements first (foreign key constraint)
            cur.execute("""
                DELETE FROM orbital_elements_cache 
                WHERE norad_id IN (
                    SELECT norad_id FROM tle_cache 
                    WHERE last_updated < %s
                );
            """, (datetime.now() - timedelta(days=max_age_days),))
            
            # Delete old TLE data
            cur.execute("""
                DELETE FROM tle_cache 
                WHERE last_updated < %s;
            """, (datetime.now() - timedelta(days=max_age_days),))
            
            deleted_count = cur.rowcount
            conn.commit()
            
            logging.info(f"Cleaned up {deleted_count} old cache entries")
            
        except Exception as e:
            logging.error(f"Error cleaning up cache: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                cur.close()
                self.connection_pool.putconn(conn)
