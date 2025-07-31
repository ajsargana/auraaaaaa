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