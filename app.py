"""
Simplified 3D Satellite Tracker using static TLE data
No live fetching, no offline caching - just smooth satellite tracking
"""
import os
import logging
from flask import Flask, render_template, jsonify, request
from satellite_data_simple import SatelliteDataManager
from datetime import datetime, timezone
from llm_chat import chat_with_llm
import time


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
        # Get observer location from query parameters for signal strength calculation
        observer_lat = float(request.args.get('lat', 0))
        observer_lon = float(request.args.get('lon', 0))
        observer_alt = float(request.args.get('alt', 0))
        
        satellite = satellite_manager.get_satellite_by_id(norad_id, observer_lat, observer_lon, observer_alt)
        
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
        
        passes = satellite_manager.get_satellite_passes(norad_id, lat, lon, int(alt))
        
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

@app.route('/api/cache/info')
def get_cache_info():
    """Get TLE cache information"""
    try:
        cache_info = satellite_manager.get_cache_info()
        
        return jsonify({
            'success': True,
            'cache_info': cache_info
        })
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/iss/live-video')
def get_iss_live_video():
    """Get ISS live video information"""
    try:
        # YouTube live stream URL for ISS
        video_info = {
            'video_url': 'https://www.youtube.com/embed/fO9e9jnhYK8?autoplay=1&mute=1&loop=1&playlist=fO9e9jnhYK8',
            'title': 'ISS Live Video Stream',
            'description': 'Live view from the International Space Station',
            'provider': 'NASA/YouTube'
        }
        
        return jsonify({
            'success': True,
            'video_info': video_info
        })
    except Exception as e:
        logger.error(f"Error getting ISS live video info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status')
def get_status():
    """Get application status"""
    try:
        satellites = satellite_manager.get_satellite_data()
        cache_info = satellite_manager.get_cache_info()
        
        return jsonify({
            'success': True,
            'status': {
                'satellites_loaded': len(satellites),
                'last_update': satellite_manager.last_update.isoformat() if satellite_manager.last_update else None,
                'cache_info': cache_info,
                'features': {
                    'smooth_movement': True,
                    'real_time_updates': True,
                    'offline_mode': False,
                    'iss_live_video': True
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Set this to True when you want to test the LLM
USE_LLM = True  # Change this to True now

@app.route("/api/chat", methods=["POST"])
def chat_api():
    print("FLASK: Chat API called!")
    start_time = time.time()

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        user_input = data.get("message")
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        print(f"FLASK: User message: '{user_input}'")

        if USE_LLM:
            # Use your improved LLM
            response = chat_with_llm(user_input)
        else:
            # Use simple responses for testing
            response = simple_chat_response(user_input)

        elapsed_time = time.time() - start_time
        print(f"FLASK: Response generated in {elapsed_time:.2f} seconds")
        print(f"FLASK: Sending response: '{response}'")

        return jsonify({"response": response})

    except Exception as e:
        print(f"FLASK: Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def simple_chat_response(user_input):
    """Fast responses for testing"""
    user_input = user_input.lower().strip()

    responses = {
        'hi': "Hello! 👋 How can I help you today?",
        'hello': "Hi there! 😊 What can I do for you?",
        'hey': "Hey! What's up?",
        'how are you': "I'm doing great! How are you doing?",
        'thanks': "You're welcome! Anything else I can help with?",
        'thank you': "Happy to help! 😊",
        'bye': "Goodbye! Have a wonderful day! 👋",
        'help': "I'm here to help! What do you need assistance with?",
    }

    for key, response in responses.items():
        if key in user_input:
            return response

    return f"I received your message: '{user_input}'. I'm currently in test mode!"




@app.route("/test")
def test():
    return "✅ Test route works!"

# Add CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


# ADD THIS CODE to your existing Flask app file
# Put it BEFORE the "if __name__ == '__main__':" line


    print("\n=== CHECKING YOUR EXISTING FLASK APP ===")
print("📍 Your existing routes:")
for rule in app.url_map.iter_rules():
    print(f"  ✅ {rule.rule} -> {rule.endpoint} ({', '.join(rule.methods or set())})")
print("=========================================\n")

if __name__ == '__main__':
    print("🛰️  3D Satellite Tracker - Starting...")
    satellites = satellite_manager.get_satellite_data()
    print(f"🌍 Satellites loaded: {len(satellites)}")
    print("🚀 Server starting on http://0.0.0.0:5000")

    app.run(host='0.0.0.0', port=5000, debug=True)
# Add this debug code to your Flask app



# Add this right after your app = Flask(__name__) line
print("\n" + "="*50)
print("🔍 FLASK TEMPLATE DEBUG")
print("="*50)
print(f"📁 Current working directory: {os.getcwd()}")
print(f"📁 Flask app root path: {app.root_path}")
print(f"📁 Template folder path: {app.template_folder}")

# Check if templates exist
templates_path = os.path.join(app.root_path, 'templates')
print(f"📁 Looking for templates in: {templates_path}")
print(f"📁 Templates folder exists: {os.path.exists(templates_path)}")

if os.path.exists(templates_path):
    template_files = os.listdir(templates_path)
    print(f"📄 Template files found: {template_files}")
else:
    print("❌ Templates folder not found!")

print("="*50 + "\n")

# Test your routes with better error handling
