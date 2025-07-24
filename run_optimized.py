#!/usr/bin/env python3
"""
Optimized local development server for 3D Satellite Tracker
Enhanced with caching, smooth movement, and better performance
"""

import os
import sys
from app_optimized import app

def main():
    # Set environment variables for local development
    if not os.environ.get('SESSION_SECRET'):
        os.environ['SESSION_SECRET'] = 'dev-secret-key-change-in-production'
    
    # Check offline mode
    offline_mode = os.environ.get('OFFLINE_MODE', 'false').lower() == 'true'
    
    print("=" * 60)
    print("🛰️  3D Satellite Tracker - Optimized Version")
    print("=" * 60)
    print(f"🚀 Starting enhanced application...")
    print(f"📡 Offline mode: {'ON' if offline_mode else 'OFF'}")
    print(f"🌐 Server: http://localhost:5000")
    print(f"🛰️  Tracker: http://localhost:5000/tracker")
    print("💾 Features: Local caching, smooth movement, optimized orbits")
    print("=" * 60)
    
    # Show cache information
    try:
        from satellite_tracker_optimized import SatelliteTrackerOptimized
        tracker = SatelliteTrackerOptimized(offline_mode=offline_mode)
        cache_status = tracker.get_cache_status()
        
        print(f"📊 Satellites loaded: {tracker.get_satellite_count()}")
        if cache_status['has_cache']:
            print(f"💾 Cache: {cache_status['satellite_count']} satellites")
            if cache_status['cache_age_days'] is not None:
                print(f"⏰ Cache age: {cache_status['cache_age_days']} days")
            if cache_status['needs_update']:
                print("⚠️  Cache needs update (will auto-update if online)")
        else:
            print("💾 Using sample data (no cache)")
            
    except Exception as e:
        print(f"⚠️  Cache check failed: {e}")
    
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Run the Flask application
        app.run(
            host='127.0.0.1',  # localhost only for security
            port=5000,
            debug=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()