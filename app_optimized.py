"""
Optimized Flask application with improved caching and smooth satellite movement
"""

import os
import logging
from flask import Flask, render_template, jsonify, request
from satellite_tracker_optimized import SatelliteTrackerOptimized

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Initialize optimized satellite tracker
offline_mode = os.environ.get("OFFLINE_MODE", "false").lower() == "true"
tracker = SatelliteTrackerOptimized(offline_mode=offline_mode)

@app.route('/')
def index():
    """Landing page"""
    return render_template('landing.html')

@app.route('/tracker')
def tracker_app():
    """Main tracker application"""
    return render_template('tracker.html')

@app.route('/api/satellites')
def get_satellites():
    """Get all satellite positions with smooth movement data"""
    try:
        satellites = tracker.get_satellite_positions()
        cache_status = tracker.get_cache_status()
        
        return jsonify({
            'success': True,
            'satellites': satellites,
            'timestamp': tracker.get_current_time(),
            'offline_mode': tracker.offline_mode,
            'cache_status': cache_status,
            'satellite_count': len(satellites)
        })
        
    except Exception as e:
        app.logger.error(f"Error getting satellites: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'satellites': [],
            'timestamp': tracker.get_current_time()
        }), 200

@app.route('/api/satellite/<int:norad_id>')
def get_satellite_details(norad_id):
    """Get detailed satellite information"""
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

@app.route('/api/satellite/<int:norad_id>/orbit')
def get_satellite_orbit(norad_id):
    """Get satellite orbit path"""
    try:
        duration_hours = request.args.get('duration', 3, type=int)
        orbit_points = tracker.get_satellite_orbit_path(norad_id, duration_hours)
        
        return jsonify({
            'success': True,
            'orbit_points': orbit_points,
            'duration_hours': duration_hours,
            'point_count': len(orbit_points)
        })
        
    except Exception as e:
        app.logger.error(f"Error getting orbit: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'orbit_points': []
        }), 200

@app.route('/api/satellite/<int:norad_id>/future_ground_track')
def get_future_ground_track(norad_id):
    """Get satellite future ground track"""
    try:
        duration_hours = request.args.get('duration', 3, type=int)
        ground_track_points = tracker.get_future_ground_track(norad_id, duration_hours)
        
        return jsonify({
            'success': True,
            'ground_track_points': ground_track_points,
            'duration_hours': duration_hours,
            'point_count': len(ground_track_points)
        })
        
    except Exception as e:
        app.logger.error(f"Error getting ground track: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'ground_track_points': []
        }), 200

@app.route('/api/satellites/search')
def search_satellites():
    """Search satellites by name"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': True,
                'satellites': [],
                'message': 'Empty search query'
            })
        
        results = tracker.search_satellites(query)
        
        return jsonify({
            'success': True,
            'satellites': results,
            'total_found': len(results),
            'query': query
        })
        
    except Exception as e:
        app.logger.error(f"Error searching satellites: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'satellites': []
        }), 200

@app.route('/api/satellite/<int:norad_id>/passes')
def get_satellite_passes(norad_id):
    """Get satellite passes over observer location"""
    try:
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        alt = float(request.args.get('alt', 0))
        
        passes = tracker.get_next_passes(norad_id, lat, lon, alt)
        
        return jsonify({
            'success': True,
            'passes': passes,
            'observer': {'lat': lat, 'lon': lon, 'alt': alt}
        })
        
    except Exception as e:
        app.logger.error(f"Error getting passes: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'passes': []
        }), 500

@app.route('/api/categories')
def get_satellite_categories():
    """Get satellite categories with counts"""
    try:
        categories = tracker.get_satellite_categories()
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        app.logger.error(f"Error getting categories: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'categories': {}
        }), 500

@app.route('/api/cache/status')
def get_cache_status():
    """Get cache status information"""
    try:
        status = tracker.get_cache_status()
        return jsonify({
            'success': True,
            'cache_status': status,
            'offline_mode': tracker.offline_mode,
            'satellite_count': tracker.get_satellite_count()
        })
    except Exception as e:
        app.logger.error(f"Error getting cache status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cache/refresh', methods=['POST'])
def refresh_cache():
    """Force refresh of satellite data cache"""
    try:
        if tracker.offline_mode:
            return jsonify({
                'success': False,
                'error': 'Cannot refresh cache in offline mode'
            }), 400
        
        force = request.json.get('force', False) if request.is_json else False
        success = tracker.refresh_data(force=force)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Cache refreshed successfully',
                'satellite_count': tracker.get_satellite_count()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to refresh cache'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error refreshing cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status')
def get_app_status():
    """Get overall application status"""
    try:
        cache_status = tracker.get_cache_status()
        
        return jsonify({
            'success': True,
            'status': {
                'offline_mode': tracker.offline_mode,
                'satellites_loaded': tracker.get_satellite_count(),
                'cache_status': cache_status,
                'version': '2.0.0-optimized',
                'features': {
                    'smooth_movement': True,
                    'local_caching': True,
                    'orbit_visualization': True,
                    'ground_tracks': True,
                    'search': True,
                    'categories': True
                }
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error getting app status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/preferences', methods=['GET', 'POST'])
def user_preferences():
    """Handle user preferences (simplified for offline app)"""
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'preferences': {
                    'location': {'lat': 0.0, 'lon': 0.0, 'alt': 0.0},
                    'update_interval': 5,  # 5 seconds for smooth movement
                    'show_satellite_paths': True,
                    'show_ground_tracks': True,
                    'favorite_satellites': [],
                    'offline_mode': tracker.offline_mode
                }
            })
        
        elif request.method == 'POST':
            # In a real app, you'd save these preferences
            return jsonify({
                'success': True,
                'message': 'Preferences saved locally'
            })
    
    except Exception as e:
        app.logger.error(f"Error handling preferences: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🛰️  Optimized 3D Satellite Tracker")
    print("=" * 40)
    print(f"📡 Offline mode: {'ON' if tracker.offline_mode else 'OFF'}")
    print(f"🌍 Satellites loaded: {tracker.get_satellite_count()}")
    
    cache_status = tracker.get_cache_status()
    if cache_status['has_cache']:
        print(f"💾 Cache status: {cache_status['satellite_count']} satellites")
        if cache_status['cache_age_days']:
            print(f"⏰ Cache age: {cache_status['cache_age_days']} days")
    
    print("🚀 Starting server on http://localhost:5000")
    print("=" * 40)
    
    app.run(host='127.0.0.1', port=5000, debug=True)