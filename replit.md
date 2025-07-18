# 3D Satellite Tracker

## Overview

This is a real-time 3D satellite tracking application built with Flask and Cesium.js. The application provides an interactive 3D globe visualization showing the current positions of satellites in Earth's orbit, with detailed tracking information and categorization of different satellite types.

## System Architecture

### Frontend Architecture
- **Cesium.js**: Primary 3D visualization engine with performance optimizations for 10fps smooth experience
- **Bootstrap**: UI framework with dark theme and enhanced visual styling
- **Enhanced JavaScript**: Performance-optimized satellite viewer with FPS monitoring and memory management
- **Font Awesome**: Icon library for comprehensive UI elements

### Backend Architecture
- **Flask**: Lightweight Python web framework with PostgreSQL database integration
- **Flask-Login & Replit Auth**: Complete authentication system with user sessions and OAuth
- **Skyfield**: Python library for astronomical calculations and satellite position tracking
- **TLE Data Integration**: Fetches Two-Line Element sets with robust error handling and caching

### Database Architecture
- **PostgreSQL**: Primary database for user management and preferences
- **User Management**: Complete user authentication with profile data and session storage
- **User Preferences**: Location settings, update intervals, and personalization options

## Key Components

### Core Backend Components
1. **SatelliteTracker Class** (`satellite_tracker.py`)
   - Manages TLE data loading and parsing from multiple sources
   - Calculates real-time satellite positions using Skyfield
   - Categorizes satellites by type (ISS, GPS, Weather, Communication, Scientific, Military)
   - Handles periodic data updates with robust caching mechanism

2. **Authentication System** (`replit_auth.py`, `models.py`)
   - Complete user authentication with Replit OAuth integration
   - User session management and security
   - User preferences storage and retrieval
   - PostgreSQL database models for users and preferences

3. **Flask Application** (`app.py`, `routes.py`)
   - Modular route structure with authentication protection
   - REST API endpoints for satellite data and user management
   - Enhanced error handling and logging
   - Performance monitoring and optimization

### Frontend Components
1. **Enhanced SatelliteViewer Class** (`satellite-viewer-enhanced.js`)
   - Optimized Cesium.js integration for 10fps smooth performance
   - Real-time FPS monitoring and memory management
   - Advanced user interaction handling (selection, tracking, filtering)
   - Geolocation integration and user preference persistence

2. **Beautiful Responsive UI** (`landing.html`, `tracker.html`)
   - Stunning landing page with animated satellite background
   - Professional tracker interface with enhanced visual design
   - Real-time status monitoring and performance indicators
   - Mobile-optimized responsive design with dark theme

## Data Flow

1. **Initialization**: Backend loads TLE data from external sources and categorizes satellites
2. **Real-time Updates**: Frontend polls `/api/satellites` endpoint every 5 minutes for position updates
3. **User Interaction**: Satellite selection triggers detailed information requests via `/api/satellite/<id>`
4. **3D Rendering**: Cesium.js renders satellite positions on Earth globe with real-time animation
5. **Filtering**: Category-based filtering allows users to focus on specific satellite types

## External Dependencies

### Backend Dependencies
- **Skyfield**: Astronomical computation library for satellite tracking
- **NumPy**: Scientific computing for orbital calculations
- **Requests**: HTTP library for fetching TLE data from external sources

### Frontend Dependencies
- **Cesium.js**: 3D globe and satellite visualization
- **Bootstrap**: UI framework
- **Font Awesome**: Icon library

### Data Sources
- **TLE Data**: Two-Line Element sets from satellite tracking databases
- **Cesium Ion**: Terrain and imagery data for Earth visualization

## Deployment Strategy

### Current Setup
- **Development Server**: Flask development server for local testing
- **Static Assets**: CSS and JavaScript served directly by Flask
- **Environment Variables**: SESSION_SECRET for Flask session management

### Production Considerations
- Recommended to use WSGI server (Gunicorn, uWSGI) for production deployment
- CDN integration for static assets
- Database integration may be added for caching satellite data and user preferences
- Rate limiting for API endpoints to prevent abuse

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Recent Updates:
- July 11, 2025: Enhanced authentication system with Replit OAuth integration
- July 11, 2025: Performance optimization for 10fps smooth visualization experience
- July 11, 2025: Beautiful UI redesign with stunning landing page and enhanced tracker interface
- July 11, 2025: PostgreSQL database integration for user management and preferences
- July 11, 2025: Real-time FPS monitoring and performance indicators
- July 11, 2025: Mobile-responsive design with dark theme enhancements
- July 03, 2025: Initial setup with basic satellite tracking functionality