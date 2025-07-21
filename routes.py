from flask import session, render_template, jsonify, request, redirect, url_for
from app import app, db, tracker
import json

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    """Landing page as intro"""
    return render_template('landing.html')

@app.route('/tracker')
def tracker_app():
    """Satellite tracker page"""
    return render_template('tracker.html')

@app.route('/landing')
def landing():
    """Landing page"""
    return render_template('landing.html')

@app.route('/api/satellites')
def get_satellites():
    """Get current positions of all satellites"""
    try:
        # Ensure tracker is initialized
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
    """Get predicted orbit path for a specific satellite"""
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

@app.route('/api/satellites/search')
def search_satellites():
    """Search satellites by name"""
    try:
        query = request.args.get('q', '').strip().lower()
        if not query:
            return jsonify({
                'success': True,
                'satellites': [],
                'message': 'Empty search query'
            })
        
        # Search satellites by name
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
            'satellites': matching_satellites[:50],  # Limit results
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
    """Get detailed information for a specific satellite"""
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
    """Get next passes for a satellite over user location"""
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
    """Get satellite categories with color coding"""
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
    """Refresh TLE data from source"""
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
    """Get or update user preferences (no authentication required)"""
    try:
        if request.method == 'GET':
            # Return default preferences for anonymous users
            return jsonify({
                'success': True,
                'preferences': {
                    'location': {'lat': 0.0, 'lon': 0.0, 'alt': 0.0},
                    'update_interval': 5,
                    'show_satellite_paths': True,
                    'favorite_satellites': []
                }
            })
        
        elif request.method == 'POST':
            # Save preferences in browser session/localStorage
            return jsonify({'success': True, 'message': 'Preferences saved locally'})
    
    except Exception as e:
        app.logger.error(f"Error handling user preferences: {e}")
        return jsonify({
            'success': False,
            'error': f"Failed to handle user preferences: {str(e)}"
        }), 500

@app.route('/api/satellite/<int:norad_id>/future_ground_track')
def get_future_ground_track(norad_id):
    """Get future ground track for a specific satellite"""
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