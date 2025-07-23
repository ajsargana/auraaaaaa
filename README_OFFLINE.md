# 3D Satellite Tracker - Offline Setup Guide

This guide will help you run the 3D Satellite Tracker application locally on your PC using VS Code, completely offline after initial setup.

## Prerequisites

1. **Python 3.11 or higher** - Download from [python.org](https://www.python.org/downloads/)
2. **VS Code** - Download from [code.visualstudio.com](https://code.visualstudio.com/)
3. **Git** (optional) - For version control

## Quick Setup Instructions

### 1. Create Project Directory
```bash
mkdir satellite-tracker
cd satellite-tracker
```

### 2. Set up Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r offline_requirements.txt
```

### 4. Set Environment Variables
Create a `.env` file in the project root:
```
SESSION_SECRET=your-secret-key-here-change-this-to-something-secure
```

Or set it directly in your terminal:
```bash
# Windows
set SESSION_SECRET=your-secret-key-here-change-this-to-something-secure

# macOS/Linux
export SESSION_SECRET=your-secret-key-here-change-this-to-something-secure
```

### 5. Run the Application
```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## Files Required for Offline Operation

Copy these files to your local project directory:

### Core Application Files
- `app.py` - Main Flask application
- `satellite_tracker.py` - Satellite tracking logic
- `offline_requirements.txt` - Python dependencies
- `offline_satellite_data.py` - Offline satellite data (created below)

### Templates (create `templates/` folder)
- `templates/landing.html` - Landing page
- `templates/tracker.html` - Main tracker interface

### Static Files (create `static/` folder)
- `static/css/style.css` - Custom styles
- `static/js/satellite-viewer-enhanced.js` - 3D visualization logic

### Configuration Files
- `run_local.py` - Local development server
- `.env` - Environment variables
- `README_OFFLINE.md` - This setup guide

## Running Without Internet

The app uses real satellite data from Celestrak by default. For completely offline operation, you'll need to:

1. **Download TLE data once** while you have internet
2. **Use the offline data file** (created below)
3. **Cache Cesium.js assets locally** (optional, for full offline operation)

## VS Code Setup

1. Open the project folder in VS Code
2. Install the Python extension
3. Select your virtual environment as the Python interpreter (Ctrl+Shift+P → "Python: Select Interpreter")
4. Create a `.vscode/launch.json` file for debugging (see below)

## Environment Variables Needed

- `SESSION_SECRET`: A secure random string for Flask sessions (required)
- No API keys needed for basic operation!

## Port Configuration

The app runs on port 5000 by default. You can change this in `app.py`:
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

## Troubleshooting

1. **Port 5000 in use**: Change the port in `app.py` or kill processes using port 5000
2. **Module not found**: Make sure your virtual environment is activated
3. **Permission errors**: Run terminal as administrator on Windows
4. **TLE data loading fails offline**: Use the offline data file provided

## File Structure
```
satellite-tracker/
├── venv/                          # Virtual environment
├── templates/
│   ├── landing.html
│   └── tracker.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── satellite-viewer-enhanced.js
├── app.py                         # Main application
├── satellite_tracker.py          # Satellite tracking logic
├── offline_satellite_data.py     # Offline satellite data
├── run_local.py                   # Local development server
├── offline_requirements.txt      # Dependencies
├── .env                          # Environment variables
└── README_OFFLINE.md             # This guide
```