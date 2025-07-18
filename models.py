from datetime import datetime
from app import db

# Simple user preferences for satellite tracking (no authentication required)
class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, nullable=False)  # Browser session ID for anonymous users
    preferred_location_lat = db.Column(db.Float, default=0.0)
    preferred_location_lon = db.Column(db.Float, default=0.0)
    preferred_location_alt = db.Column(db.Float, default=0.0)
    preferred_update_interval = db.Column(db.Integer, default=10)  # seconds
    show_satellite_paths = db.Column(db.Boolean, default=True)
    favorite_satellites = db.Column(db.Text)  # JSON string of NORAD IDs
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)