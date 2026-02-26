"""
Satellite category definitions and classification logic
Separated for better organization and faster updates
"""

class SatelliteCategories:
    def __init__(self):
        self.categories = self._define_categories()
    
    def _define_categories(self):
        """Define satellite categories with colors and patterns"""
        return {
            'ISS': {
                'name': 'International Space Station',
                'color': '#FF6B6B',
                'satellites': [],
                'keywords': ['ISS', 'ZARYA', 'INTERNATIONAL SPACE STATION']
            },
            'GPS': {
                'name': 'GPS Constellation',
                'color': '#4ECDC4',
                'satellites': [],
                'keywords': ['GPS', 'NAVSTAR', 'BIIR', 'BIIF', 'BIII']
            },
            'GLONASS': {
                'name': 'GLONASS Navigation',
                'color': '#FF8C42',
                'satellites': [],
                'keywords': ['GLONASS', 'COSMOS']
            },
            'Galileo': {
                'name': 'Galileo Navigation',
                'color': '#6A4C93',
                'satellites': [],
                'keywords': ['GALILEO', 'GSAT']
            },
            'BeiDou': {
                'name': 'BeiDou Navigation',
                'color': '#F25C54',
                'satellites': [],
                'keywords': ['BEIDOU', 'COMPASS']
            },
            'Weather': {
                'name': 'Weather Satellites',
                'color': '#45B7D1',
                'satellites': [],
                'keywords': ['NOAA', 'GOES', 'METEOSAT', 'FENGYUN', 'WEATHER', 'HIMAWARI']
            },
            'Earth_Observation': {
                'name': 'Earth Observation',
                'color': '#52B788',
                'satellites': [],
                'keywords': ['LANDSAT', 'SENTINEL', 'SPOT', 'WORLDVIEW', 'QUICKBIRD', 'TERRA', 'AQUA', 'MODIS']
            },
            'Communication': {
                'name': 'Communication Satellites',
                'color': '#96CEB4',
                'satellites': [],
                'keywords': ['INTELSAT', 'EUTELSAT', 'ASTRA', 'HISPASAT', 'TURKSAT', 'NILESAT', 'ARABSAT']
            },
            'Starlink': {
                'name': 'Starlink Constellation',
                'color': '#E9C46A',
                'satellites': [],
                'keywords': ['STARLINK']
            },
            'OneWeb': {
                'name': 'OneWeb Constellation',
                'color': '#F4A261',
                'satellites': [],
                'keywords': ['ONEWEB', 'ONE WEB']
            },
            'Iridium': {
                'name': 'Iridium Constellation',
                'color': '#E76F51',
                'satellites': [],
                'keywords': ['IRIDIUM']
            },
            'Scientific': {
                'name': 'Scientific Satellites',
                'color': '#B5838D',
                'satellites': [],
                'keywords': ['HUBBLE', 'CHANDRA', 'SPITZER', 'KEPLER', 'TESS', 'SWIFT', 'JWST']
            },
            'Military': {
                'name': 'Military Satellites',
                'color': '#8D5524',
                'satellites': [],
                'keywords': ['DSP', 'NOSS', 'LACROSSE', 'MENTOR', 'TRUMPET', 'OPS']
            },
            'Geostationary': {
                'name': 'Geostationary Satellites',
                'color': '#F77F00',
                'satellites': [],
                'keywords': []  # Determined by orbital characteristics
            },
            'Debris': {
                'name': 'Space Debris',
                'color': '#8B4513',
                'satellites': [],
                'keywords': ['DEB', 'DEBRIS', 'FRAG', 'FRAGMENT', 'R/B', 'ROCKET BODY']
            },
            'Inactive': {
                'name': 'Inactive Satellites',
                'color': '#696969',
                'satellites': [],
                'keywords': ['DEAD', 'INACTIVE', 'DECOMMISSIONED', 'NON-OP']
            },
            'Other': {
                'name': 'Other Satellites',
                'color': '#A8A8A8',
                'satellites': [],
                'keywords': []
            }
        }
    
    def categorize_satellite(self, name, altitude=None):
        """Categorize satellite based on name and orbital characteristics"""
        name_upper = name.upper()
        
        # Check each category's keywords
        for category_id, category_info in self.categories.items():
            if category_id == 'Other':  # Skip 'Other' category in keyword matching
                continue
            
            for keyword in category_info['keywords']:
                if keyword in name_upper:
                    return category_id
        
        # Special case: Geostationary satellites (altitude > 35,000 km)
        if altitude and altitude > 35000:
            return 'Geostationary'
        
        return 'Other'
    
    def get_category_info(self, category_id):
        """Get category information"""
        return self.categories.get(category_id, self.categories['Other'])
    
    def get_all_categories(self):
        """Get all categories with their information"""
        categories = {}
        for cat_id, cat_info in self.categories.items():
            categories[cat_id] = {
                'name': cat_info['name'],
                'color': cat_info['color'],
                'count': len(cat_info['satellites'])
            }
        return categories

def categorize_satellite(name):
    """
    Categorize a satellite based on its name and return category and color
    """
    name_upper = name.upper()
    
    # ISS and Space Stations
    if any(keyword in name_upper for keyword in ['ISS', 'ZARYA', 'INTERNATIONAL SPACE STATION']):
        return 'iss', '#FF6B6B'
    
    # GPS/GNSS
    if any(keyword in name_upper for keyword in ['GPS', 'NAVSTAR', 'BIIR', 'BIIF', 'BIII']):
        return 'gps', '#4ECDC4'
    if any(keyword in name_upper for keyword in ['GLONASS', 'COSMOS']):
        return 'glonass', '#FF8C42'
    if any(keyword in name_upper for keyword in ['GALILEO', 'GSAT']):
        return 'galileo', '#6A4C93'
    if any(keyword in name_upper for keyword in ['BEIDOU', 'COMPASS']):
        return 'beidou', '#F25C54'
    
    # Weather
    if any(keyword in name_upper for keyword in ['NOAA', 'GOES', 'METEOSAT', 'FENGYUN', 'WEATHER', 'HIMAWARI']):
        return 'weather', '#45B7D1'
    
    # Earth Observation (comprehensive)
    if any(keyword in name_upper for keyword in [
        'LANDSAT', 'SENTINEL', 'SPOT', 'WORLDVIEW', 'QUICKBIRD', 'GEOEYE', 'IKONOS', 
        'PLEIADES', 'KOMPSAT', 'ALOS', 'RADARSAT', 'COSMO-SKYMED', 'TERRASAR', 
        'PAZ', 'ENVISAT', 'ERS', 'CBERS', 'RESOURCESAT', 'CARTOSAT', 'RISAT',
        'TERRA', 'AQUA', 'MODIS', 'PROBA', 'DEIMOS', 'DUBAISAT', 'ALSAT',
        'NIGERIASAT', 'BILSAT', 'EGYPTSAT', 'FALCON EYE', 'KONDOR', 'KANOPUS',
        'RESURS', 'METEOR-M', 'ELECTRO', 'YAOGAN', 'GAOFEN', 'ZIYUAN', 'TIANHUI',
        'JILIN', 'SUPERVIEW', 'PLANETSCOPE', 'RAPIDEYE', 'SKYSAT', 'DOVE', 'FLOCK',
        'PLANET', 'BLACKSKY', 'ICEYE', 'CAPELLA', 'UMBRA', 'EROS', 'VENUS', 'OFEK'
    ]):
        return 'earth_observation', '#52B788'
    
    # Communication
    if any(keyword in name_upper for keyword in ['INTELSAT', 'EUTELSAT', 'ASTRA', 'HISPASAT', 'TURKSAT', 'NILESAT', 'ARABSAT']):
        return 'communication', '#96CEB4'
    
    # Starlink
    if 'STARLINK' in name_upper:
        return 'starlink', '#E9C46A'
    
    # OneWeb
    if any(keyword in name_upper for keyword in ['ONEWEB', 'ONE WEB']):
        return 'oneweb', '#F4A261'
    
    # Iridium
    if 'IRIDIUM' in name_upper:
        return 'iridium', '#E76F51'
    
    # Scientific
    if any(keyword in name_upper for keyword in ['SCIENCE', 'RESEARCH', 'EXPERIMENT', 'HUBBLE', 'SPITZER', 'KEPLER']):
        return 'scientific', '#9B59B6'
    
    # Military/Intelligence (comprehensive)
    if any(keyword in name_upper for keyword in [
        'NROL', 'USA-', 'LACROSSE', 'ONYX', 'MISTY', 'MENTOR', 'TRUMPET', 'MERCURY',
        'CRYSTAL', 'KEYHOLE', 'KH-', 'ORION', 'FIA', 'AEHF', 'MILSTAR', 'DSCS',
        'WGS', 'WIDEBAND', 'UFO', 'SBIRS', 'DSP', 'DEFENSE', 'EARLY WARNING',
        'NOSS', 'WHITE CLOUD', 'PARCAE', 'ELINT', 'SIGINT', 'MAGNUM', 'CHALET',
        'RHYOLITE', 'AQUACADE', 'CANYON', 'JUMPSEAT', 'FERRET', 'POPPY', 'GRAB',
        'PERSONA', 'YANTAR', 'ALMAZ', 'OKEAN', 'KONDOR-E', 'LOTOS', 'LIANA',
        'TUNDRA', 'EKS', 'BARS', 'PION', 'MILITARY', 'CLASSIFIED', 'RECONNAISSANCE',
        'SURVEILLANCE', 'INTELLIGENCE', 'DEFENSE', 'SECURITY', 'SPY'
    ]) or name_upper.startswith('USA '):
        return 'military', '#E74C3C'
    
    # Space Debris
    if any(keyword in name_upper for keyword in ['DEB', 'DEBRIS', 'FRAG', 'FRAGMENT', 'R/B', 'ROCKET BODY']):
        return 'debris', '#8B4513'
    
    # Inactive satellites
    if any(keyword in name_upper for keyword in ['DEAD', 'INACTIVE', 'DECOMMISSIONED', 'NON-OP']):
        return 'inactive', '#696969'
    
    # Default - Other/Unknown
    return 'other', '#95A5A6'
    
    def add_satellite_to_category(self, category_id, norad_id):
        """Add satellite to category"""
        if category_id in self.categories:
            if norad_id not in self.categories[category_id]['satellites']:
                self.categories[category_id]['satellites'].append(norad_id)
    
    def clear_all_categories(self):
        """Clear all satellites from categories"""
        for category in self.categories.values():
            category['satellites'].clear()