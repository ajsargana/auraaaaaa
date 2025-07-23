#!/usr/bin/env python3
"""
Local development server for 3D Satellite Tracker
Run this file to start the application locally in VS Code
"""

import os
import sys
from app import app

def main():
    # Set default environment variables for local development
    if not os.environ.get('SESSION_SECRET'):
        os.environ['SESSION_SECRET'] = 'dev-secret-key-change-in-production'
    
    print("=" * 60)
    print("🛰️  3D Satellite Tracker - Local Development Server")
    print("=" * 60)
    print(f"🚀 Starting application...")
    print(f"📡 Server will be available at: http://localhost:5000")
    print(f"🌐 Landing page: http://localhost:5000/")
    print(f"🛰️  Tracker page: http://localhost:5000/tracker")
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