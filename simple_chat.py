# Simple chat bot for satellite tracking app
import json
import re
from datetime import datetime

class SimpleChatBot:
    def __init__(self, satellite_tracker):
        self.tracker = satellite_tracker
        self.conversation_history = []
        
        # Predefined responses for common satellite tracking questions
        self.responses = {
            'greeting': [
                "Hello! I'm your satellite tracking assistant. I can help you find satellites, check their positions, and explain orbital mechanics.",
                "Hi there! Ask me about satellites, their orbits, or how to track them.",
                "Welcome! I can help you explore the world of satellite tracking. What would you like to know?"
            ],
            'satellite_count': "There are currently {} satellites being tracked in our system.",
            'iss': "The International Space Station (ISS) is one of the largest satellites. It orbits Earth about every 90 minutes at an altitude of approximately 400km.",
            'help': "I can help you with:\n• Finding specific satellites\n• Explaining satellite categories\n• Checking current satellite positions\n• Understanding orbital mechanics\n• Pass predictions for your location",
            'categories': "Satellites are categorized into: Communication, Weather, Navigation (GPS), Scientific, Military, and Amateur radio satellites.",
            'orbit': "Satellites orbit Earth at different altitudes: Low Earth Orbit (LEO) 160-2000km, Medium Earth Orbit (MEO) 2000-35,786km, and Geostationary Orbit (GEO) at 35,786km.",
            'tracking': "Satellite tracking uses Two-Line Element (TLE) data that contains orbital parameters. This data is updated regularly to predict satellite positions.",
        }
    
    def get_response(self, user_input):
        """Generate a response based on user input"""
        user_input_lower = user_input.lower().strip()
        
        # Add to conversation history
        self.conversation_history.append({
            'user': user_input,
            'timestamp': datetime.now().isoformat()
        })
        
        response = self._analyze_input(user_input_lower)
        
        # Add response to history
        self.conversation_history.append({
            'bot': response,
            'timestamp': datetime.now().isoformat()
        })
        
        return response
    
    def _analyze_input(self, user_input):
        """Analyze user input and provide appropriate response"""
        
        # Greeting patterns
        if any(word in user_input for word in ['hello', 'hi', 'hey', 'start']):
            return self.responses['greeting'][0]
        
        # Help patterns
        elif any(word in user_input for word in ['help', 'what can you do', 'commands']):
            return self.responses['help']
        
        # Satellite count
        elif any(phrase in user_input for phrase in ['how many satellites', 'satellite count', 'number of satellites']):
            count = self.tracker.get_satellite_count() if self.tracker else "12,000+"
            return self.responses['satellite_count'].format(count)
        
        # ISS specific
        elif any(word in user_input for word in ['iss', 'international space station', 'space station']):
            return self.responses['iss']
        
        # Categories
        elif any(word in user_input for word in ['categories', 'types', 'kinds of satellites']):
            return self.responses['categories']
        
        # Orbit information
        elif any(word in user_input for word in ['orbit', 'altitude', 'height', 'distance']):
            return self.responses['orbit']
        
        # Tracking information
        elif any(word in user_input for word in ['track', 'tracking', 'tle', 'how does it work']):
            return self.responses['tracking']
        
        # Search for specific satellite
        elif any(word in user_input for word in ['find', 'search', 'look for', 'where is']):
            return self._handle_satellite_search(user_input)
        
        # Location/pass predictions
        elif any(word in user_input for word in ['pass', 'visible', 'see', 'location']):
            return "To get satellite pass predictions, please set your location using the location button in the app. I can then tell you when satellites will be visible from your location."
        
        # Default responses for common question patterns
        elif '?' in user_input:
            return "That's an interesting question about satellites! Try asking me about satellite types, orbital mechanics, or how to track specific satellites."
        
        else:
            return "I'm here to help with satellite tracking! Ask me about satellites, their orbits, categories, or how to find specific ones. Type 'help' to see what I can do."
    
    def _handle_satellite_search(self, user_input):
        """Handle satellite search requests"""
        # Extract potential satellite name from input
        words = user_input.split()
        # Remove common words to find satellite name
        common_words = ['find', 'search', 'look', 'for', 'where', 'is', 'the', 'satellite']
        satellite_words = [word for word in words if word.lower() not in common_words]
        
        if satellite_words:
            satellite_name = ' '.join(satellite_words).upper()
            return f"To find {satellite_name}, use the search box in the app interface. I can see all tracked satellites, but you'll need to use the 3D viewer to see their current positions and orbits."
        else:
            return "Please specify which satellite you'd like to find. For example: 'find ISS' or 'search for Hubble telescope'."
    
    def get_conversation_history(self):
        """Return conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []