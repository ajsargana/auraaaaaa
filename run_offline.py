#!/usr/bin/env python3
"""
Run the offline satellite tracker application
"""
import os
import logging
from app_offline import app, tracker

# Configure logging
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    # Force offline mode
    os.environ['OFFLINE_MODE'] = 'true'
    
    print("🛰️  Offline 3D Satellite Tracker")
    print("=" * 40)
    print(f"📡 Offline mode: {'ON' if tracker.offline_mode else 'OFF'}")
    print(f"🌍 Satellites loaded: {len(tracker.satellites) if hasattr(tracker, 'satellites') else 0}")
    print("🚀 Starting offline server on http://0.0.0.0:5001")
    print("=" * 40)
    
    app.run(host='0.0.0.0', port=5001, debug=True)