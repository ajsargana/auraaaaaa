import os
import logging
from flask import Flask, render_template, jsonify, request
from satellite_tracker_offline import SatelliteTracker

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Initialize satellite tracker with offline mode option
offline_mode = os.environ.get("OFFLINE_MODE", "false").lower() == "true"
tracker = SatelliteTracker(offline_mode=offline_mode)

# Routes
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
            'timestamp': tracker.get_current_time(),
            'offline_mode': tracker.offline_mode
        })
    except Exception as e:
        app.logger.error(f"Error getting satellite positions: {e}")
        return jsonify({
            'success': False,
            'error': f"Failed to load satellites: {str(e)}",
            'satellites': [],
            'timestamp': tracker.get_current_time(),
            'offline_mode': tracker.offline_mode
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

@app.route('/api/satellite/<int:norad_id>/future_ground_track')
def get_future_ground_track(norad_id):
    try:
        duration_hours = request.args.get('duration', 3, type=int)
        ground_track_points = tracker.get_future_ground_track(norad_id, duration_hours)
        
        return jsonify({
            'success': True,
            'ground_track_points': ground_track_points,
            'duration_hours': duration_hours
        })
    except Exception as e:
        app.logger.error(f"Error getting future ground track: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'ground_track_points': []
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
        if tracker.offline_mode:
            return jsonify({
                'success': False,
                'error': 'Cannot refresh TLE data in offline mode'
            }), 400
        
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
                    'favorite_satellites': [],
                    'offline_mode': tracker.offline_mode
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

@app.route('/api/status')
def get_status():
    """Get application status"""
    return jsonify({
        'success': True,
        'status': {
            'offline_mode': tracker.offline_mode,
            'satellites_loaded': len(tracker.satellites),
            'last_update': tracker.last_update.isoformat() if tracker.last_update else None,
            'categories': len(tracker.categories),
            'version': '1.0.0'
        }
    })

if __name__ == '__main__':
    print("🛰️  3D Satellite Tracker - Starting...")
    print(f"📡 Offline mode: {'ON' if tracker.offline_mode else 'OFF'}")
    print(f"🌍 Satellites loaded: {len(tracker.satellites)}")
    print("🚀 Server starting on http://localhost:5000")
    
    app.run(host='127.0.0.1', port=5000, debug=True)