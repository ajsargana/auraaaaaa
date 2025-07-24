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
    
    def add_satellite_to_category(self, category_id, norad_id):
        """Add satellite to category"""
        if category_id in self.categories:
            if norad_id not in self.categories[category_id]['satellites']:
                self.categories[category_id]['satellites'].append(norad_id)
    
    def clear_all_categories(self):
        """Clear all satellites from categories"""
        for category in self.categories.values():
            category['satellites'].clear()