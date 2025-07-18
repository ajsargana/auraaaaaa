from flask import session, render_template, jsonify, request, redirect, url_for
from app import app, db, tracker
import json

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    """Main page with 3D satellite visualization"""
    return render_template('tracker.html')

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

@app.route('/api/satellite/<int:norad_id>/orbit')
def get_satellite_orbit(norad_id):
    """Get orbital path for a specific satellite"""
    try:
        orbit_points = tracker.get_orbital_path(norad_id)
        return jsonify({
            'success': True,
            'orbit': orbit_points
        })
    except Exception as e:
        app.logger.error(f"Error getting satellite orbit: {e}")
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
    """Get or update user preferences"""
    try:
        if request.method == 'GET':
            # Return default preferences for all users
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
            # For now, just return success without saving to database
            return jsonify({'success': True, 'message': 'Preferences saved locally'})
    
    except Exception as e:
        app.logger.error(f"Error handling user preferences: {e}")
        return jsonify({
            'success': False,
            'error': f"Failed to handle user preferences: {str(e)}"
        }), 500