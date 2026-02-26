"""
AI Chat Module - Dedicated module for satellite tracking AI assistant
Provides intelligent responses about satellites, space missions, and orbital mechanics
"""

import random
import re
import time
import requests
import json
from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger(__name__)

class AIAssistant:
    """Main AI Assistant class for satellite tracking application"""

    def __init__(self, satellite_database=None):
        self.satellite_database = satellite_database
        self.conversation_history = []
        import os
        self.gemini_config = {
            'api_key': os.environ.get('GEMINI_API_KEY', ''),
            'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent',
            'rate_limit': 60,
            'timeout': 15,
            'max_tokens': 200,
            'retry_attempts': 2
        }
        self.rate_tracker = {
            'requests_made': 0,
            'window_start': time.time(),
            'is_available': True,
            'last_reset': time.time()
        }
        self.system_prompt = """You are an intelligent AI Agent for a 3D Satellite Tracking web application.

Your role is to provide helpful information about satellites and space.

You have access to a database of 943+ satellites including:
- ISS, Starlink, GPS satellites
- Weather satellites (NOAA, GOES)
- Earth observation (Landsat, Sentinel, Hubble)
- Scientific and communication satellites

Provide clear, informative responses about satellites, space missions, and orbital mechanics.

Keep responses conversational and under 150 words.

DO NOT include any JSON formatting, code blocks, or special markup in your response.
Just provide a natural, helpful answer."""

    def set_satellite_database(self, database):
        """Set the satellite database reference"""
        self.satellite_database = database

    def process_message(self, user_input, chat_type='agent'):
        """Process user message and return appropriate response based on AI personality"""
        try:
            # Check rate limit
            if not self._check_rate_limit():
                return self._create_fallback_response(user_input, chat_type)

            # Get conversation context
            context = self._get_conversation_context()

            # Try Gemini API first with personality-specific prompt
            response = self._try_gemini_api(user_input, context, chat_type)

            if response:
                # Add to conversation history
                self._add_to_conversation_history(user_input, response)
                return response
            else:
                # Fall back to local response
                fallback_response = self._create_fallback_response(user_input, chat_type)
                self._add_to_conversation_history(user_input, fallback_response)
                return fallback_response

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            fallback_response = "I'm experiencing some technical difficulties. Let me help you with satellite information instead!"
            self._add_to_conversation_history(user_input, fallback_response)
            return fallback_response

    def _create_response(self, action, message, extra_data=None):
        """Create a standardized response format"""
        response_data = {
            "action": action,
            "message": message
        }
        if extra_data:
            response_data.update(extra_data)
        return json.dumps(response_data)

    def _create_fallback_response(self, user_input, chat_type='agent'):
        """Generate fallback response when API is unavailable, tailored to AI personality"""
        user_lower = user_input.lower()

        if chat_type == 'kepler':
            # Kepler provides detailed technical information
            if any(keyword in user_lower for keyword in ['iss', 'international space station']):
                return "The International Space Station (ISS) is a habitable artificial satellite orbiting at approximately 408 km altitude. It completes 15.5 orbits per day, traveling at 27,600 km/h. The ISS serves as a microgravity research laboratory where astronauts conduct experiments in materials science, biology, and physics. It's a joint project between NASA, Roscosmos, ESA, JAXA, and CSA."

            elif any(keyword in user_lower for keyword in ['starlink', 'spacex']):
                return "Starlink is SpaceX's mega-constellation of small satellites in Low Earth Orbit (LEO) at altitudes between 340-1,200 km. Each satellite weighs about 260 kg and uses Ka and Ku bands for communication. The constellation aims to provide global broadband internet with low latency due to the shorter signal path compared to geostationary satellites."

            elif any(keyword in user_lower for keyword in ['gps', 'navigation']):
                return "The Global Positioning System (GPS) consists of 31 satellites in Medium Earth Orbit (MEO) at 20,200 km altitude. They orbit in 6 planes inclined at 55° to the equator. Each satellite broadcasts L1 (1575.42 MHz) and L2 (1227.60 MHz) signals. The system requires 4 satellites for 3D positioning using trilateration principles."

            elif any(keyword in user_lower for keyword in ['weather', 'noaa', 'goes']):
                return "NOAA's GOES satellites operate in geostationary orbit at 35,786 km altitude. GOES-16 and GOES-17 provide continuous weather monitoring for the Western Hemisphere. They carry the Advanced Baseline Imager (ABI) with 16 spectral bands and the Geostationary Lightning Mapper (GLM) for storm detection."

            elif any(keyword in user_lower for keyword in ['hubble', 'telescope']):
                return "The Hubble Space Telescope orbits at 547 km altitude in a low-inclination orbit. It carries a 2.4-meter primary mirror and instruments including the Wide Field Camera 3 and Space Telescope Imaging Spectrograph. Hubble has made over 1.5 million observations and discovered that the universe's expansion is accelerating."

        else:
            # Agent provides action-oriented responses
            if any(keyword in user_lower for keyword in ['show', 'find', 'select', 'track']):
                return "I can help you find and select satellites in the SkyScope interface! Try asking me to 'show the ISS' or 'find Starlink satellites'. I can control the 3D view, apply filters, and focus the camera on specific satellites."

            elif any(keyword in user_lower for keyword in ['search', 'filter', 'category']):
                return "I can help you search and filter satellites! I can apply filters by country, agency, orbit type, or mission category. Just tell me what you're looking for, like 'show me weather satellites' or 'filter by SpaceX'."

            elif any(keyword in user_lower for keyword in ['iss', 'international space station']):
                return "I can show you the ISS location and track it in real-time! The International Space Station is one of the most tracked objects. Would you like me to focus the camera on it and show its current position?"

        # Common responses for both personalities
        if any(keyword in user_lower for keyword in ['altitude', 'orbit', 'orbital']):
            return "Satellite orbits are classified by altitude: Low Earth Orbit (LEO) 160-2000km for Earth observation and communications, Medium Earth Orbit (MEO) 2000-35,786km for navigation like GPS, and Geostationary Orbit (GEO) at 35,786km for weather and communications satellites that stay above one point on Earth."

        elif any(keyword in user_lower for keyword in ['how many', 'count', 'number']):
            if self.satellite_database:
                sat_data = self.satellite_database.get_satellite_data()
                count = len(sat_data) if sat_data else 0
                return f"Our SkyScope database currently tracks {count} active satellites from agencies worldwide, including communication satellites, Earth observation missions, navigation systems, weather monitoring, and scientific research platforms."
            return "SkyScope tracks nearly 1000 satellites including communication, navigation, weather, and scientific research satellites from agencies worldwide."

        # Default responses based on personality
        if chat_type == 'kepler':
            default_responses = [
                "I'm Kepler, your satellite expert! I can provide detailed technical information about satellites, space missions, orbital mechanics, and space technology. What would you like to learn about?",
                "As a space mission specialist, I can explain satellite specifications, launch details, orbital parameters, and mission objectives. Ask me about any satellite or space program!",
                "I have extensive knowledge about satellites from all major space agencies - NASA, ESA, Roscosmos, SpaceX, and more. What technical details interest you?"
            ]
        else:
            default_responses = [
                "I'm your AI Agent for SkyScope! I can control the interface, search for satellites, apply filters, and help you navigate the 3D view. What would you like me to do?",
                "I can help you explore satellites in SkyScope by controlling the interface, finding specific satellites, or applying filters. Just tell me what you want to see!",
                "Ready to assist with SkyScope navigation! I can select satellites, focus the camera, apply filters, and control the visualization. How can I help?"
            ]

        return random.choice(default_responses)


    def _search_satellites_in_db(self, query):
        """Search for satellites in the database"""
        if not self.satellite_database:
            return []

        try:
            satellites = self.satellite_database.get_satellite_data()
            matching_satellites = []
            query_lower = query.lower().strip()

            for satellite in satellites:
                name_lower = satellite['name'].lower()
                score = 0

                if query_lower == name_lower:
                    score = 100
                elif query_lower in name_lower:
                    score = 80
                elif name_lower.startswith(query_lower):
                    score = 70
                elif all(word in name_lower for word in query_lower.split()):
                    score = 60
                elif any(word in name_lower for word in query_lower.split() if len(word) > 2):
                    score = 40

                if score > 0:
                    matching_satellites.append({
                        'satellite': satellite,
                        'score': score,
                        'name': satellite['name']
                    })

            matching_satellites.sort(key=lambda x: x['score'], reverse=True)
            return [item['satellite'] for item in matching_satellites[:15]]

        except Exception as e:
            logger.error(f"Error searching satellites: {e}")
            return []

    def _get_satellite_info_from_db(self, satellite_name):
        """Get detailed information about a satellite"""
        if not self.satellite_database:
            return None

        try:
            satellites = self.satellite_database.get_satellite_data()
            for satellite in satellites:
                if satellite_name.upper() in satellite['name'].upper():
                    detailed_info = self.satellite_database.get_satellite_by_id(satellite['norad_id'])
                    return detailed_info
            return None
        except Exception as e:
            logger.error(f"Error getting satellite info: {e}")
            return None

    def _should_use_gemini(self, user_input):
        """Decide whether to use Gemini API or local patterns"""
        user_input_lower = user_input.lower().strip()

        # Simple patterns - use local responses
        simple_patterns = [
            r'^\b(hi|hello|hey|hiya|howdy)\b!?$',
            r'^\b(thanks|thank you|thx)\b!?$',
            r'^\b(bye|goodbye|see you|cya)\b!?$',
            r'^\bhow\s+are\s+you\b\??$',
            r'^\bwhat\'?s\s+up\b\??$',
            r'^\b(hi|hello|hey)\s+(there|bot|assistant)\b!?$'
        ]

        for pattern in simple_patterns:
            if re.match(pattern, user_input_lower):
                return False

        # Space/satellite topics - use Gemini
        space_indicators = [
            r'\b(satellite|orbit|iss|space|station|tracking)\b',
            r'\b(altitude|speed|trajectory|apogee|perigee)\b',
            r'\b(international\s+space\s+station)\b',
            r'\b(landsat|molniya|geostationary|polar)\b',
            r'\b(nasa|esa|spacex|rocket)\b'
        ]

        for pattern in space_indicators:
            if re.search(pattern, user_input_lower):
                return True

        # Question patterns - use Gemini
        question_patterns = [
            r'\b(what|why|how|when|where|which|who)\b.*\?',
            r'\b(explain|tell\s+me|describe|define)\b'
        ]

        for pattern in question_patterns:
            if re.search(pattern, user_input_lower):
                return True

        return False

    def _get_local_response(self, user_input):
        """Get response from local patterns"""
        user_input_lower = user_input.lower()

        response_patterns = {
            'greetings': {
                'patterns': [r'\b(hi|hello|hey|hiya|howdy)\b'],
                'responses': [
                    "Hello! Welcome to the satellite tracker. How can I help you?",
                    "Hi there! Need help with satellite tracking?",
                    "Hey! I'm here to assist with your satellite tracking needs.",
                    "Hello! Ready to explore the world of satellites? What would you like to know?"
                ]
            },
            'iss_questions': {
                'patterns': [r'\biss\b', r'international\s+space\s+station'],
                'responses': [
                    "The ISS (International Space Station) is a large laboratory orbiting Earth at about 408 km altitude. It completes one orbit every 90 minutes and is home to astronauts conducting scientific research!",
                    "The International Space Station is humanity's outpost in space! It orbits Earth every 90 minutes at 17,500 mph, serving as a research laboratory where astronauts live and work."
                ]
            },
            'starlink_questions': {
                'patterns': [r'\bstarlink\b'],
                'responses': [
                    "Starlink is SpaceX's satellite constellation providing global internet coverage. There are thousands of Starlink satellites in low Earth orbit, typically around 550 km altitude.",
                    "Starlink satellites form a mega-constellation for global internet access. They orbit at about 550 km altitude and have orbital periods of roughly 90 minutes."
                ]
            },
            'thanks': {
                'patterns': [r'\b(thank|thanks|thx|appreciate)\b'],
                'responses': [
                    "You're welcome! Happy to help with satellite tracking!",
                    "My pleasure! Enjoy exploring the satellites!",
                    "Glad I could help! Feel free to ask more satellite questions anytime."
                ]
            },
            'goodbye': {
                'patterns': [r'\b(bye|goodbye|see\s+you|farewell|exit|quit)\b'],
                'responses': [
                    "Goodbye! Happy satellite tracking!",
                    "See you later! Keep exploring the cosmos!",
                    "Farewell! Come back anytime to track more satellites!"
                ]
            }
        }

        for category, data in response_patterns.items():
            for pattern in data['patterns']:
                if re.search(pattern, user_input_lower):
                    return random.choice(data['responses'])

        return None

    def _check_rate_limit(self):
        """Check if we're within Gemini API rate limits"""
        current_time = time.time()

        if current_time - self.rate_tracker['window_start'] >= 60:
            self.rate_tracker['requests_made'] = 0
            self.rate_tracker['window_start'] = current_time
            self.rate_tracker['is_available'] = True

        if self.rate_tracker['requests_made'] >= self.gemini_config['rate_limit']:
            self.rate_tracker['is_available'] = False
            return False

        return True

    def _try_gemini_api(self, user_input, context="", chat_type='agent'):
        """Try to get response from Gemini API with personality-specific prompts"""
        try:
            # Update rate tracker
            self.rate_tracker['requests_made'] += 1

            # Choose system prompt based on chat type
            if chat_type == 'kepler':
                system_prompt = """You are Kepler, a knowledgeable satellite and space mission expert.

Your role is to provide detailed, accurate information about:
- Satellites and their specifications
- Space missions and their objectives
- Orbital mechanics and space technology
- Space agencies and their programs
- Historical and current space exploration

You have access to information about 995+ satellites including ISS, Starlink, GPS, weather satellites, Earth observation satellites, and scientific missions.

Provide detailed, educational responses about space technology and missions. You are NOT responsible for controlling any interface - you only provide information and explanations.

Keep responses informative but conversational, under 200 words.

DO NOT include any JSON formatting, code blocks, or special markup in your response.
Just provide a natural, informative answer."""
            else:
                system_prompt = self.system_prompt

            # Build prompt
            full_prompt = f"{system_prompt}\n\n{context}\nUser: {user_input}\nAI:"

            # Prepare request data
            request_data = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": self.gemini_config['max_tokens'],
                    "stopSequences": []
                },
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
                ]
            }

            # Make API request
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': self.gemini_config['api_key']
            }

            response = requests.post(
                self.gemini_config['endpoint'], 
                json=request_data, 
                headers=headers, 
                timeout=self.gemini_config['timeout']
            )

            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    if 'content' in data['candidates'][0] and 'parts' in data['candidates'][0]['content']:
                        ai_response = data['candidates'][0]['content']['parts'][0]['text'].strip()
                        logger.info(f"Gemini API response received successfully for {chat_type}")
                        return ai_response

                logger.warning("Gemini API: No valid response content")
                return None

            else:
                logger.warning(f"Gemini API error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.Timeout:
            logger.warning("Gemini API request timed out")
            return None
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None

    def _enhanced_web_search(self, query):
        """Enhanced web search functionality"""
        try:
            search_results = []

            # Try DuckDuckGo API
            try:
                ddg_url = "https://api.duckduckgo.com/"
                params = {
                    'q': f"{query} satellite space",
                    'format': 'json',
                    'no_html': '1',
                    'skip_disambig': '1'
                }

                response = requests.get(ddg_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()

                    if data.get('Abstract'):
                        search_results.append(data['Abstract'][:300])

                    for topic in data.get('RelatedTopics', [])[:3]:
                        if isinstance(topic, dict) and 'Text' in topic:
                            search_results.append(topic['Text'][:200])
            except (requests.RequestException, ValueError, KeyError) as e:
                logger.warning(f"DuckDuckGo search failed: {e}")

            # Search in satellite database
            db_results = self._search_satellites_in_db(query)
            if db_results:
                db_info = f"Found {len(db_results)} satellites in our database: "
                db_info += ", ".join([sat['name'] for sat in db_results[:3]])
                search_results.append(db_info)

            if search_results:
                return " | ".join(search_results)
            else:
                return f"I searched for '{query}' but couldn't find detailed web results. However, I can help with satellites in our tracking database!"

        except Exception as e:
            logger.error(f"Search error: {e}")
            return f"Search encountered an issue, but I can help with satellites in our database!"

    def _add_to_conversation_history(self, user_input, ai_response):
        """Add exchange to conversation history"""
        if len(self.conversation_history) >= 10:
            self.conversation_history.pop(0)

        self.conversation_history.append({
            'user': user_input,
            'ai': ai_response,
            'timestamp': time.time()
        })

    def _get_conversation_context(self):
        """Get recent conversation context"""
        if not self.conversation_history:
            return ""

        context = "Recent conversation:\n"
        for exchange in self.conversation_history[-3:]:
            context += f"User: {exchange['user']}\nAI: {exchange['ai']}\n"

        return context

# Global instance
ai_assistant = AIAssistant()

def initialize_ai_system(satellite_database):
    """Initialize the AI system with satellite database"""
    global ai_assistant
    ai_assistant.set_satellite_database(satellite_database)
    logger.info("AI chat system initialized with satellite database")

def process_chat_message(user_input, chat_type='agent'):
    """Main function to process chat messages"""
    global ai_assistant
    return ai_assistant.process_message(user_input, chat_type)

# Legacy compatibility functions
def chat_with_llm(user_input):
    """Legacy compatibility function"""
    return process_chat_message(user_input)

def set_satellite_database(database):
    """Legacy compatibility function"""
    initialize_ai_system(database)

# Export functions for backward compatibility
__all__ = [
    'AIAssistant',
    'ai_assistant',
    'initialize_ai_system',
    'process_chat_message',
    'chat_with_llm',
    'set_satellite_database'
]