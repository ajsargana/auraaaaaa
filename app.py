
import os
import logging
from flask import Flask, session, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from satellite_tracker import SatelliteTracker
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "dev-secret-key-change-in-production"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database (optional - can work without database)
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    db.init_app(app)

# Initialize satellite tracker
tracker = SatelliteTracker()

# Simple user preferences model (no authentication required)
class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, nullable=False)
    preferred_location_lat = db.Column(db.Float, default=0.0)
    preferred_location_lon = db.Column(db.Float, default=0.0)
    preferred_location_alt = db.Column(db.Float, default=0.0)
    preferred_update_interval = db.Column(db.Integer, default=10)
    show_satellite_paths = db.Column(db.Boolean, default=True)
    favorite_satellites = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

if database_url:
    with app.app_context():
        db.create_all()

# Routes
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/tracker')
def tracker_app():
    return render_template('tracker.html')

@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route('/api/satellites')
def get_satellites():
    try:
        if not hasattr(tracker, 'satellites') or not tracker.satellites:
            tracker.load_tle_data()
        
        satellites = tracker.get_satellite_positions()
        return jsonify({
            'success': True,
            'satellites': satellites,
            'timestamp': tracker.get_current_time()
        })
    except Exception as e:
        app.logger.error(f"Error getting satellite positions: {e}")
        return jsonify({
            'success': False,
            'error': f"Failed to load satellites: {str(e)}",
            'satellites': [],
            'timestamp': tracker.get_current_time()
        }), 200

@app.route('/api/satellite/<int:norad_id>/orbit')
def get_satellite_orbit(norad_id):
    try:
        duration_hours = request.args.get('duration', 3, type=int)
        orbit_points = tracker.get_satellite_orbit_path(norad_id, duration_hours)
        
        return jsonify({
            'success': True,
            'orbit_points': orbit_points,
            'duration_hours': duration_hours
        })
    except Exception as e:
        app.logger.error(f"Error getting satellite orbit: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'orbit_points': []
        }), 200

@app.route('/api/satellite/<int:norad_id>/ground-track')
def get_satellite_ground_track(norad_id):
    try:
        duration_hours = request.args.get('duration', 3, type=int)
        swath_width = request.args.get('swath_width', 300, type=int)
        ground_track = tracker.get_satellite_ground_track(norad_id, duration_hours, swath_width)
        
        return jsonify({
            'success': True,
            'ground_track': ground_track,
            'duration_hours': duration_hours,
            'swath_width_km': swath_width
        })
    except Exception as e:
        app.logger.error(f"Error getting satellite ground track: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'ground_track': []
        }), 200

@app.route('/api/satellites/search')
def search_satellites():
    try:
        query = request.args.get('q', '').strip().lower()
        if not query:
            return jsonify({
                'success': True,
                'satellites': [],
                'message': 'Empty search query'
            })
        
        matching_satellites = []
        for norad_id, sat_data in tracker.satellites.items():
            if query in sat_data['name'].lower():
                matching_satellites.append({
                    'norad_id': norad_id,
                    'name': sat_data['name'],
                    'category': sat_data['category']
                })
        
        return jsonify({
            'success': True,
            'satellites': matching_satellites[:50],
            'total_found': len(matching_satellites)
        })
    except Exception as e:
        app.logger.error(f"Error searching satellites: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'satellites': []
        }), 200

@app.route('/api/satellite/<int:norad_id>')
def get_satellite_details(norad_id):
    try:
        details = tracker.get_satellite_details(norad_id)
        if details:
            return jsonify({
                'success': True,
                'satellite': details
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Satellite not found'
            }), 404
    except Exception as e:
        app.logger.error(f"Error getting satellite details: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/satellite/<int:norad_id>/passes')
def get_satellite_passes(norad_id):
    try:
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        alt = float(request.args.get('alt', 0))
        
        passes = tracker.get_next_passes(norad_id, lat, lon, alt)
        return jsonify({
            'success': True,
            'passes': passes
        })
    except Exception as e:
        app.logger.error(f"Error getting satellite passes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/categories')
def get_satellite_categories():
    try:
        categories = tracker.get_satellite_categories()
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        app.logger.error(f"Error getting satellite categories: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/refresh')
def refresh_tle_data():
    try:
        tracker.refresh_tle_data()
        return jsonify({
            'success': True,
            'message': 'TLE data refreshed successfully'
        })
    except Exception as e:
        app.logger.error(f"Error refreshing TLE data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/preferences', methods=['GET', 'POST'])
def user_preferences():
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'preferences': {
                    'location': {'lat': 0.0, 'lon': 0.0, 'alt': 0.0},
                    'update_interval': 1,
                    'show_satellite_paths': True,
                    'favorite_satellites': []
                }
            })
        
        elif request.method == 'POST':
            return jsonify({'success': True, 'message': 'Preferences saved locally'})
    
    except Exception as e:
        app.logger.error(f"Error handling user preferences: {e}")
        return jsonify({
            'success': False,
            'error': f"Failed to handle user preferences: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
