# 🛰️ 3D Satellite Tracker - Complete Offline Deployment Guide

## Files You Need to Copy to Your PC

### Core Application Files
```
📁 Your Local Directory/
├── app_offline.py                    # Main Flask application (offline-capable)
├── satellite_tracker_offline.py     # Satellite tracking with offline support
├── offline_satellite_data.py        # Sample satellite data for offline use
├── run_local.py                     # Simple local development server
├── setup_offline.py                # Complete setup automation script
```

### Template Files (create `templates/` folder)
```
📁 templates/
├── landing.html                     # Beautiful animated landing page
└── tracker.html                     # Main 3D satellite tracker interface
```

### Static Assets (create `static/` folder)
```
📁 static/
├── css/
│   └── style.css                    # Custom styles and animations
└── js/
    └── satellite-viewer-enhanced.js # 3D Cesium.js visualization engine
```

### Configuration Files
```
📁 Configuration/
├── offline_requirements.txt         # Python dependencies
├── .env                            # Environment variables (create manually)
├── requirements.txt                # Auto-generated pip requirements
├── run_windows.bat                 # Windows launcher script
├── run_unix.sh                     # Mac/Linux launcher script
```

### VS Code Setup (create `.vscode/` folder)
```
📁 .vscode/
├── launch.json                     # Debug configuration
└── settings.json                   # Python environment settings
```

### Documentation
```
📁 Documentation/
├── README_OFFLINE.md               # Detailed setup instructions
├── INSTALLATION.md                 # Complete installation guide
└── OFFLINE_DEPLOYMENT_GUIDE.md     # This file
```

## Environment Variables Needed

Create a `.env` file with these variables:

```bash
# REQUIRED: Flask session security (change this!)
SESSION_SECRET=your-very-secure-random-string-here-at-least-32-characters

# OPTIONAL: Force offline mode
OFFLINE_MODE=false

# OPTIONAL: Debug mode
FLASK_DEBUG=true
```

### Important: No API Keys Required!
This application works completely without external API keys. It downloads satellite data from public sources.

## Quick Setup Commands

### Option 1: Automated Setup (Recommended)
```bash
# 1. Copy all files to your directory
# 2. Run the setup script
python setup_offline.py

# 3. Launch the application
python run_local.py
```

### Option 2: Manual Setup
```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r offline_requirements.txt

# 4. Set environment variable
# Windows:
set SESSION_SECRET=your-secure-key-here
# Mac/Linux:
export SESSION_SECRET=your-secure-key-here

# 5. Run application
python app_offline.py
```

## Internet vs Offline Operation

### With Internet (Default)
- Downloads fresh satellite data from Celestrak
- Gets real-time orbital information
- Updates satellite positions accurately

### Without Internet (Offline Mode)
- Uses cached satellite data from `data/offline_tle_data.txt`
- Falls back to sample data if no cached data exists
- All features work except data refresh

### Force Offline Mode
Set in `.env` file:
```
OFFLINE_MODE=true
```

Or run with environment variable:
```bash
OFFLINE_MODE=true python app_offline.py
```

## Python Dependencies Required

```
flask>=3.1.1          # Web framework
gunicorn>=23.0.0       # Production server
numpy>=2.3.1           # Scientific computing
requests>=2.32.4       # HTTP requests
skyfield>=1.53         # Astronomical calculations
python-dotenv>=1.0.0   # Environment variables
```

## VS Code Setup Instructions

1. **Open project folder** in VS Code
2. **Install Python extension** if not already installed
3. **Select Python interpreter**: 
   - Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
   - Type "Python: Select Interpreter"
   - Choose your virtual environment: `./venv/bin/python`

4. **Debug configuration** is already provided in `.vscode/launch.json`
5. **Run/Debug**: Press `F5` to start debugging

## Application URLs

Once running, access these URLs:

- **Landing Page**: `http://localhost:5000/`
- **3D Satellite Tracker**: `http://localhost:5000/tracker`
- **API Status**: `http://localhost:5000/api/status`
- **Satellite Data**: `http://localhost:5000/api/satellites`

## Troubleshooting

### Port 5000 in Use
Change port in `app_offline.py` or `run_local.py`:
```python
app.run(host='127.0.0.1', port=8000, debug=True)
```

### Python Not Found
- Install Python 3.11+ from python.org
- Ensure Python is in your system PATH

### Module Import Errors
- Activate virtual environment first
- Reinstall dependencies: `pip install -r offline_requirements.txt`

### Satellite Data Not Loading
- Check internet connection for fresh data
- Verify `data/offline_tle_data.txt` exists for offline mode
- Sample data is embedded in `offline_satellite_data.py` as fallback

### Performance Issues
- Use Chrome or Firefox browsers
- Update graphics drivers for WebGL
- Close other browser tabs
- Reduce browser zoom level

## Features Available Offline

✅ **Full 3D Satellite Visualization**
✅ **Real-time Position Tracking**
✅ **Orbital Path Prediction**
✅ **Ground Track Visualization**
✅ **Satellite Search and Filtering**
✅ **Category Organization**
✅ **Detailed Satellite Information**
✅ **Pass Prediction (basic)**

## Data Sources

- **Online**: Celestrak.org TLE data (public, no API key needed)
- **Offline**: Cached data in `data/offline_tle_data.txt`
- **Fallback**: Sample data in `offline_satellite_data.py`

## Security Notes

- Application runs on localhost (127.0.0.1) by default
- No external connections required for offline operation
- No personal data collection
- No user authentication required
- Change SESSION_SECRET for production use

## File Size Requirements

- **Total application**: ~5MB
- **With satellite data**: ~7MB  
- **Virtual environment**: ~150MB
- **Browser cache**: ~50MB

## Platform Compatibility

✅ **Windows 10/11**
✅ **macOS 10.15+**
✅ **Linux (Ubuntu, Debian, etc.)**
✅ **Python 3.11+**
✅ **Chrome, Firefox, Safari, Edge**

## Next Steps After Setup

1. **Test the application** with sample data
2. **Download fresh TLE data** using `python offline_satellite_data.py`
3. **Customize satellite categories** in `satellite_tracker_offline.py`
4. **Add more data sources** if needed
5. **Deploy to production** using gunicorn

Enjoy your offline satellite tracking experience! 🛰️🌍