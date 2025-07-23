#!/usr/bin/env python3
"""
Setup script for offline 3D Satellite Tracker
This script helps prepare the application for offline use by downloading fresh TLE data
"""

import os
import requests
import shutil
from pathlib import Path

def create_directory_structure():
    """Create necessary directories"""
    directories = [
        "templates",
        "static/css", 
        "static/js",
        "data",
        ".vscode"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def download_tle_data():
    """Download fresh TLE data for offline use"""
    print("🛰️  Downloading fresh TLE data...")
    
    tle_sources = [
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=noaa&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=goes&FORMAT=tle",
    ]
    
    all_tle_data = []
    
    for i, url in enumerate(tle_sources, 1):
        try:
            print(f"📡 Downloading from source {i}/{len(tle_sources)}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            all_tle_data.append(response.text)
            print(f"✅ Success: {len(response.text)} characters")
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    if all_tle_data:
        combined_data = "\n".join(all_tle_data)
        with open("data/offline_tle_data.txt", "w") as f:
            f.write(combined_data)
        print(f"💾 Saved {len(combined_data)} characters to data/offline_tle_data.txt")
        return True
    else:
        print("❌ No data downloaded")
        return False

def create_env_file():
    """Create .env file with default settings"""
    env_content = """# 3D Satellite Tracker Environment Variables

# Flask session secret (REQUIRED - change this to a secure random string)
SESSION_SECRET=your-secure-secret-key-change-this-in-production

# Offline mode (set to "true" to use only local data)
OFFLINE_MODE=false

# Debug mode (set to "false" for production)
FLASK_DEBUG=true

# Application settings
FLASK_APP=app_offline.py
FLASK_ENV=development
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file with default settings")
    else:
        print("ℹ️  .env file already exists - skipping")

def create_requirements_file():
    """Create requirements.txt for pip installation"""
    requirements_content = """flask>=3.1.1
gunicorn>=23.0.0
numpy>=2.3.1
requests>=2.32.4
skyfield>=1.53
python-dotenv>=1.0.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements_content)
    print("✅ Created requirements.txt")

def create_run_script():
    """Create platform-specific run scripts"""
    
    # Windows batch file
    windows_script = """@echo off
echo 🛰️  3D Satellite Tracker - Windows Launcher
echo ==========================================

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\\Scripts\\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Starting application...
python app_offline.py

pause
"""
    
    # Unix shell script
    unix_script = """#!/bin/bash
echo "🛰️  3D Satellite Tracker - Unix Launcher"
echo "========================================"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting application..."
python app_offline.py
"""
    
    with open("run_windows.bat", "w") as f:
        f.write(windows_script)
    print("✅ Created run_windows.bat")
    
    with open("run_unix.sh", "w") as f:
        f.write(unix_script)
    os.chmod("run_unix.sh", 0o755)  # Make executable
    print("✅ Created run_unix.sh")

def create_installation_guide():
    """Create detailed installation guide"""
    guide_content = """# 3D Satellite Tracker - Complete Installation Guide

## System Requirements
- Python 3.11 or higher
- Internet connection (for initial setup only)
- 500MB free disk space
- Modern web browser with WebGL support

## Quick Start (Windows)
1. Double-click `run_windows.bat`
2. Wait for installation to complete
3. Open browser to http://localhost:5000

## Quick Start (Mac/Linux)
1. Run `./run_unix.sh` in terminal
2. Wait for installation to complete  
3. Open browser to http://localhost:5000

## Manual Installation

### Step 1: Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\\Scripts\\activate

# Mac/Linux
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment
Edit `.env` file and set a secure SESSION_SECRET:
```
SESSION_SECRET=your-very-secure-random-string-here
```

### Step 4: Run Application
```bash
# For online mode (downloads fresh satellite data)
python app_offline.py

# For offline mode (uses cached data only)
OFFLINE_MODE=true python app_offline.py
```

### Step 5: Open Browser
Navigate to: http://localhost:5000

## File Structure
```
satellite-tracker/
├── venv/                     # Python virtual environment
├── templates/               
│   ├── landing.html         # Landing page
│   └── tracker.html         # Main application
├── static/
│   ├── css/style.css        # Styles
│   └── js/satellite-viewer-enhanced.js  # 3D visualization
├── data/
│   └── offline_tle_data.txt # Cached satellite data
├── app_offline.py           # Main application
├── satellite_tracker_offline.py  # Satellite logic
├── offline_satellite_data.py     # Sample data
├── requirements.txt         # Dependencies
├── .env                     # Environment variables
├── run_windows.bat         # Windows launcher
├── run_unix.sh            # Unix launcher
└── README.md              # This guide
```

## Environment Variables
- `SESSION_SECRET`: Flask session secret (required)
- `OFFLINE_MODE`: Set to "true" for offline operation
- `FLASK_DEBUG`: Set to "false" for production

## Troubleshooting

### Port 5000 Already in Use
Change port in `app_offline.py`:
```python
app.run(host='127.0.0.1', port=8000, debug=True)
```

### Python Module Not Found
Ensure virtual environment is activated:
```bash
# Windows
venv\\Scripts\\activate

# Mac/Linux  
source venv/bin/activate
```

### Internet Connection Issues
Set offline mode in `.env`:
```
OFFLINE_MODE=true
```

### Performance Issues
- Close other browser tabs
- Update your graphics drivers
- Use Chrome or Firefox for best performance

## Features
- ✅ Real-time 3D satellite visualization
- ✅ Orbital path prediction (3 hours)
- ✅ Ground track visualization
- ✅ Satellite search and filtering
- ✅ Category-based organization
- ✅ Offline operation support
- ✅ No database required
- ✅ No external API keys needed

## Data Sources
- Celestrak.org TLE data (when online)
- Cached local data (when offline)
- Sample data included for testing

Enjoy tracking satellites! 🛰️
"""
    
    with open("INSTALLATION.md", "w") as f:
        f.write(guide_content)
    print("✅ Created INSTALLATION.md")

def main():
    """Main setup function"""
    print("🛰️  3D Satellite Tracker - Offline Setup")
    print("=" * 50)
    
    # Create directory structure
    create_directory_structure()
    
    # Create configuration files
    create_env_file()
    create_requirements_file()
    
    # Create run scripts
    create_run_script()
    
    # Create documentation
    create_installation_guide()
    
    # Try to download fresh TLE data
    if download_tle_data():
        print("✅ Fresh TLE data downloaded successfully")
    else:
        print("ℹ️  Using sample TLE data (offline_satellite_data.py)")
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Copy all application files to this directory")
    print("2. Run 'run_windows.bat' (Windows) or './run_unix.sh' (Unix)")
    print("3. Open http://localhost:5000 in your browser")
    print("\nFor detailed instructions, see INSTALLATION.md")

if __name__ == "__main__":
    main()