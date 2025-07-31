"""
Simplified 3D Satellite Tracker using static TLE data
No live fetching, no offline caching - just smooth satellite tracking
"""
import os
import logging
from flask import Flask, render_template, jsonify, request
from satellite_data_simple import SatelliteDataManager
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize satellite data manager
satellite_manager = SatelliteDataManager()

# Initialize data on startup
logger.info("Initializing satellite data...")
if not satellite_manager.load_tle_data():
    logger.error("Failed to load satellite data")

@app.route('/')
def landing():
    """Landing page"""
    return render_template('landing.html')

@app.route('/tracker')
def tracker():
    """Main tracker page"""
    return render_template('tracker.html')

@app.route('/api/satellites')
def get_satellites():
    """Get all satellite data"""
    try:
        satellites = satellite_manager.get_satellite_data()
        
        return jsonify({
            'success': True,
            'satellites': satellites,
            'satellite_count': len(satellites),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'offline_mode': False,
            'cache_status': {
                'has_cache': True,
                'last_update': satellite_manager.last_update.isoformat() if satellite_manager.last_update else None,
                'satellite_count': len(satellites)
            }
        })
    except Exception as e:
        logger.error(f"Error getting satellites: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'satellites': [],
            'satellite_count': 0
        }), 500

@app.route('/api/satellite/<int:norad_id>')
def get_satellite_details(norad_id):
    """Get detailed information for a specific satellite"""
    try:
        satellite = satellite_manager.get_satellite_by_id(norad_id)
        
        if not satellite:
            return jsonify({
                'success': False,
                'error': 'Satellite not found'
            }), 404
            
        return jsonify({
            'success': True,
            'satellite': satellite
        })
    except Exception as e:
        logger.error(f"Error getting satellite {norad_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/categories')
def get_categories():
    """Get satellite categories"""
    try:
        categories = satellite_manager.get_categories()
        
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'categories': {}
        }), 500

@app.route('/api/satellites/search')
def search_satellites():
    """Search satellites by name"""
    try:
        query = request.args.get('q', '').strip().lower()
        
        if not query or len(query) < 2:
            return jsonify({
                'success': True,
                'satellites': [],
                'query': query
            })
        
        satellites = satellite_manager.get_satellite_data()
        matching_satellites = [
            sat for sat in satellites 
            if query in sat['name'].lower()
        ]
        
        # Limit results to 50 for performance
        matching_satellites = matching_satellites[:50]
        
        return jsonify({
            'success': True,
            'satellites': matching_satellites,
            'query': query,
            'total_matches': len(matching_satellites)
        })
    except Exception as e:
        logger.error(f"Error searching satellites: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'satellites': []
        }), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """Refresh satellite data"""
    try:
        success = satellite_manager.refresh_data()
        
        if success:
            satellites = satellite_manager.get_satellite_data()
            return jsonify({
                'success': True,
                'message': 'Data refreshed successfully',
                'satellite_count': len(satellites),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to refresh data'
            }), 500
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/satellite/<int:norad_id>/orbit')
def get_satellite_orbit(norad_id):
    """Get satellite orbit path"""
    try:
        duration = int(request.args.get('duration', 3))
        orbit_points = satellite_manager.get_satellite_orbit(norad_id, duration)
        
        if orbit_points:
            return jsonify({
                'success': True,
                'orbit_points': orbit_points
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Satellite not found or no orbit data available'
            }), 404
    except Exception as e:
        logger.error(f"Error getting satellite orbit {norad_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/satellite/<int:norad_id>/ground-track')
def get_satellite_ground_track(norad_id):
    """Get satellite ground track"""
    try:
        duration = int(request.args.get('duration', 3))
        swath_width = int(request.args.get('swath_width', 300))
        ground_track = satellite_manager.get_satellite_ground_track(norad_id, duration, swath_width)
        
        if ground_track:
            return jsonify({
                'success': True,
                'ground_track': ground_track
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Satellite not found or no ground track data available'
            }), 404
    except Exception as e:
        logger.error(f"Error getting satellite ground track {norad_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/satellite/<int:norad_id>/passes')
def get_satellite_passes(norad_id):
    """Get satellite pass predictions"""
    try:
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        alt = float(request.args.get('alt', 0))
        
        passes = satellite_manager.get_satellite_passes(norad_id, lat, lon, alt)
        
        return jsonify({
            'success': True,
            'passes': passes
        })
    except Exception as e:
        logger.error(f"Error getting satellite passes {norad_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/preferences', methods=['GET', 'POST'])
def user_preferences():
    """Get or set user preferences"""
    if request.method == 'GET':
        # Return default preferences for now
        return jsonify({
            'success': True,
            'preferences': {
                'location': {'lat': 0, 'lon': 0, 'alt': 0},
                'update_interval': 10
            }
        })
    else:
        # POST - save preferences (mock implementation)
        return jsonify({
            'success': True,
            'message': 'Preferences saved'
        })

@app.route('/api/status')
def get_status():
    """Get application status"""
    try:
        satellites = satellite_manager.get_satellite_data()
        
        return jsonify({
            'success': True,
            'status': {
                'satellites_loaded': len(satellites),
                'last_update': satellite_manager.last_update.isoformat() if satellite_manager.last_update else None,
                'features': {
                    'smooth_movement': True,
                    'real_time_updates': True,
                    'offline_mode': False
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)