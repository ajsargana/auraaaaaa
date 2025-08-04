# llm_chat.py - Enhanced system with Gemini API integration
import random
import re
import time
import requests
import json
from datetime import datetime, timedelta

print("Loading enhanced chat system with Gemini API...")

# Gemini API Configuration
GEMINI_CONFIG = {
    'api_key': 'AIzaSyDWM-6BSWwusmuXB5eY5bSaylprZqWOBn0',
    'endpoint': 'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent',
    'rate_limit': 60,
    'timeout': 15,
    'max_tokens': 100,
    'retry_attempts': 2
}

# Rate limiting tracker
rate_tracker = {
    'requests_made': 0,
    'window_start': time.time(),
    'is_available': True,
    'last_reset': time.time()
}

# System prompt for Gemini
SATELLITE_SYSTEM_PROMPT = """You are an AI assistant for a 3D Satellite Tracking web application. 

🎯 YOUR ROLE: Answer satellite and space questions concisely and helpfully.

📝 RESPONSE RULES:
- Keep answers under 80 words
- Be enthusiastic about space/satellites
- Use relevant emojis: 🛰️ 🚀 🌍 ⭐ 🌌
- Give practical, accurate information
- If asked about non-space topics, politely redirect to satellites/space

✅ GOOD TOPICS: ISS, satellites, orbits, space stations, orbital mechanics, satellite tracking, astronomy, space technology

❌ AVOID: Long explanations, non-space topics, speculation about classified satellites"""

# Basic response patterns for simple interactions
RESPONSE_PATTERNS = {
    'greetings': {
        'patterns': [r'\b(hi|hello|hey|hiya|howdy)\b'],
        'responses': [
            "Hello! 👋 Welcome to the satellite tracker. How can I help you?",
            "Hi there! 🛰️ Need help with satellite tracking?",
            "Hey! I'm here to assist with your satellite tracking needs.",
            "Hello! Ready to explore the world of satellites? What would you like to know?"
        ]
    },
    'status': {
        'patterns': [r'how\s+are\s+you', r'how\s+do\s+you\s+do', r'what\'?s\s+up'],
        'responses': [
            "I'm running smoothly! 🚀 All satellite tracking systems are operational.",
            "Doing great! Ready to help you track satellites and explore space data.",
            "I'm online and ready to assist! What satellite information do you need?",
            "All systems green! 🟢 How can I help with your satellite tracking today?"
        ]
    },
    'thanks': {
        'patterns': [r'\b(thank|thanks|thx|appreciate)\b'],
        'responses': [
            "You're welcome! 😊 Happy to help with satellite tracking!",
            "My pleasure! 🌟 Enjoy exploring the satellites!",
            "Glad I could help! Feel free to ask more satellite questions anytime.",
            "You're very welcome! Keep tracking those satellites! 🛰️"
        ]
    },
    'goodbye': {
        'patterns': [r'\b(bye|goodbye|see\s+you|farewell|exit|quit)\b'],
        'responses': [
            "Goodbye! 👋 Happy satellite tracking!",
            "See you later! 🚀 Keep exploring the cosmos!",
            "Farewell! Come back anytime to track more satellites!",
            "Bye! 🌟 Hope you enjoyed your satellite tracking session!"
        ]
    }
}

# Local satellite knowledge for when API fails
SATELLITE_FACTS = {
    'iss_basic': {
        'patterns': [r'\bwhat\s+is\s+(the\s+)?iss\b', r'\binternational\s+space\s+station\b'],
        'responses': [
            "The ISS (International Space Station) is a large spacecraft orbiting Earth! 🛰️ It's a laboratory where astronauts live and work, about 408 km above us. You can often see it with the naked eye!",
            "The International Space Station is humanity's outpost in space! 🚀 It orbits Earth every 90 minutes at 17,500 mph. It's as big as a football field and home to astronauts from around the world! 🌍"
        ]
    },
    'iss_speed': {
        'patterns': [r'\b(speed|velocity|fast)\b.*\biss\b', r'\biss\b.*\b(speed|velocity|fast)\b'],
        'responses': [
            "The ISS travels at approximately 17,500 mph (28,000 km/h)! 🚀 That's fast enough to go around Earth in just 90 minutes. It's zooming through space right now! 🛰️",
            "The International Space Station speeds around Earth at 7.66 kilometers per second! ⚡ That means it completes one orbit every 90 minutes - incredible speed! 🌍"
        ]
    },
    'satellite_general': {
        'patterns': [r'\bsatellite\b', r'\borbital\b', r'\borbit\b'],
        'responses': [
            "Satellites are incredible machines orbiting Earth! 🛰️ There are thousands up there - communication satellites, weather satellites, GPS satellites, and more. Each serves a unique purpose! 🌍",
            "Satellites follow different orbital paths depending on their mission! 🚀 Some are in low Earth orbit like the ISS, others in geostationary orbit staying above one spot. Fascinating orbital mechanics! ⭐"
        ]
    },
    'tracking_help': {
        'patterns': [r'\btrack\b', r'\bfind\b.*\bsatellite\b', r'\bvisible\b'],
        'responses': [
            "This satellite tracker shows real-time positions of satellites! 🛰️ You can find the ISS, Starlink satellites, and many others. The tracker updates their positions as they orbit Earth! 🌍",
            "Great question about tracking! 🔍 This app displays satellites as they orbit overhead. You can see which ones are visible from your location and when they'll pass by! ⭐"
        ]
    }
}

def check_rate_limit():
    """Check if we're within Gemini API rate limits"""
    global rate_tracker

    current_time = time.time()

    # Reset counter every minute
    if current_time - rate_tracker['window_start'] >= 60:
        rate_tracker['requests_made'] = 0
        rate_tracker['window_start'] = current_time
        rate_tracker['is_available'] = True
        print("GEMINI: Rate limit window reset")

    # Check if we're under the limit
    if rate_tracker['requests_made'] >= GEMINI_CONFIG['rate_limit']:
        rate_tracker['is_available'] = False
        print("GEMINI: Rate limit reached, falling back to local responses")
        return False

    return True

def should_use_gemini(user_input):
    """Decide whether to use Gemini API or local patterns"""
    user_input_lower = user_input.lower().strip()

    # Always use local patterns for simple cases
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
            print("ROUTING: '" + user_input + "' -> LOCAL (simple greeting/response)")
            return False

    # Use Gemini for satellite/space questions
    space_indicators = [
        r'\b(satellite|orbit|iss|space|station|tracking)\b',
        r'\b(altitude|speed|trajectory|apogee|perigee)\b',
        r'\b(international\s+space\s+station)\b',
        r'\b(landsat|molniya|geostationary|polar)\b',
        r'\b(nasa|esa|spacex|rocket)\b'
    ]

    for pattern in space_indicators:
        if re.search(pattern, user_input_lower):
            print("ROUTING: '" + user_input + "' -> GEMINI (space/satellite topic)")
            return True

    # Use Gemini for question words
    question_patterns = [
        r'\b(what|why|how|when|where|which|who)\b.*\?',
        r'\b(explain|tell\s+me|describe|define)\b'
    ]

    for pattern in question_patterns:
        if re.search(pattern, user_input_lower):
            print("ROUTING: '" + user_input + "' -> GEMINI (question/explanation needed)")
            return True

    # Default to local patterns
    print("ROUTING: '" + user_input + "' -> LOCAL (default)")
    return False

def get_local_response(user_input):
    """Get response from patterns and satellite facts"""
    user_input_lower = user_input.lower()

    # Check basic response patterns first
    for category, data in RESPONSE_PATTERNS.items():
        for pattern in data['patterns']:
            if re.search(pattern, user_input_lower):
                response = random.choice(data['responses'])
                print("LOCAL: Found " + category + " pattern -> '" + response[:50] + "...'")
                return response

    # Check satellite knowledge base
    for category, data in SATELLITE_FACTS.items():
        for pattern in data['patterns']:
            if re.search(pattern, user_input_lower):
                response = random.choice(data['responses'])
                print("LOCAL: Found " + category + " satellite fact -> '" + response[:50] + "...'")
                return response

    print("LOCAL: No pattern match found")
    return None

def call_gemini_api(user_input):
    """Call Gemini API with retry logic and better error handling"""
    global rate_tracker

    for attempt in range(GEMINI_CONFIG['retry_attempts']):
        try:
            # Check rate limits first
            if not check_rate_limit():
                print("GEMINI: Rate limited, attempt " + str(attempt + 1))
                return None

            # Prepare the request
            headers = {
                'Content-Type': 'application/json'
            }

            # Gemini request format
            payload = {
                "contents": [{
                    "parts": [{
                        "text": SATELLITE_SYSTEM_PROMPT + "\n\nUser: " + user_input
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": GEMINI_CONFIG['max_tokens']
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH", 
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }

            # Make the API call
            api_url = GEMINI_CONFIG['endpoint'] + "?key=" + GEMINI_CONFIG['api_key']

            print("GEMINI: Attempt " + str(attempt + 1) + "/" + str(GEMINI_CONFIG['retry_attempts']) + " for: '" + user_input[:50] + "...'")
            start_time = time.time()

            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=GEMINI_CONFIG['timeout']
            )

            response_time = time.time() - start_time
            print("GEMINI: API responded in " + str(round(response_time, 2)) + " seconds")

            # Update rate tracker
            rate_tracker['requests_made'] += 1

            # Check response
            if response.status_code == 200:
                data = response.json()

                # Extract the response text from Gemini's format
                if 'candidates' in data and len(data['candidates']) > 0:
                    candidate = data['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        content = candidate['content']['parts'][0]['text'].strip()
                        print("GEMINI: Success! Response: '" + content[:100] + "...'")
                        return content

                print("GEMINI: Unexpected response format")

            else:
                print("GEMINI: API Error " + str(response.status_code) + ": " + response.text)

        except requests.exceptions.Timeout:
            print("GEMINI: Request timeout on attempt " + str(attempt + 1))
            if attempt < GEMINI_CONFIG['retry_attempts'] - 1:
                print("GEMINI: Retrying with shorter timeout...")
                time.sleep(1)
            continue

        except requests.exceptions.RequestException as e:
            print("GEMINI: Request error on attempt " + str(attempt + 1) + ": " + str(e))
            if attempt < GEMINI_CONFIG['retry_attempts'] - 1:
                time.sleep(1)
            continue

        except Exception as e:
            print("GEMINI: Unexpected error on attempt " + str(attempt + 1) + ": " + str(e))
            break

    print("GEMINI: All " + str(GEMINI_CONFIG['retry_attempts']) + " attempts failed")
    return None

def chat_with_llm(user_input):
    """Enhanced chat function with smart routing and reliable fallbacks"""
    print("ENHANCED: Processing '" + user_input + "'")

    # Clean input
    user_input = user_input.strip()
    if not user_input:
        return "Please send me a message! I'm here to help with satellite tracking. 🛰️"

    # Handle very short inputs
    if len(user_input) <= 2:
        return "Could you tell me a bit more? I'm here to help with satellite tracking questions!"

    try:
        # Smart routing: local first for simple queries
        if not should_use_gemini(user_input):
            print("ENHANCED: Using local patterns for simple query")
            local_response = get_local_response(user_input)
            if local_response:
                return local_response

        # Try Gemini for complex queries
        if check_rate_limit():
            print("ENHANCED: Using Gemini API for complex query")
            gemini_response = call_gemini_api(user_input)

            if gemini_response:
                return gemini_response
            else:
                print("ENHANCED: Gemini failed, checking local satellite knowledge")
        else:
            print("ENHANCED: Rate limited, using local responses")

        # Fallback 1: Check local satellite knowledge
        local_response = get_local_response(user_input)
        if local_response:
            return local_response

        # Fallback 2: Smart contextual responses based on input
        user_lower = user_input.lower()

        if any(word in user_lower for word in ['iss', 'international', 'space', 'station']):
            return "The ISS is an amazing space station! 🛰️ It orbits Earth every 90 minutes at 17,500 mph. Unfortunately, my detailed knowledge system is temporarily unavailable, but I can help you track it on this app! 🚀"

        elif any(word in user_lower for word in ['satellite', 'orbit', 'tracking']):
            return "Satellites are fascinating! 🛰️ There are thousands orbiting Earth right now. While my detailed database is temporarily offline, this tracker can show you their real-time positions! 🌍"

        elif any(word in user_lower for word in ['speed', 'fast', 'velocity']):
            return "Space objects move incredibly fast! 🚀 Satellites typically orbit at speeds of thousands of miles per hour. The ISS, for example, travels at 17,500 mph! ⚡"

        elif any(word in user_lower for word in ['molniya', 'geostationary', 'polar', 'landsat']):
            return "That's a great question about orbital mechanics! 🛰️ Different satellites use different types of orbits depending on their mission. I'd love to give you detailed info, but my knowledge system is temporarily unavailable. 🌍"

        # Ultimate fallback - still helpful and contextual
        fallback_responses = [
            "I understand you're asking about '" + user_input + "' - that's a great satellite/space question! 🛰️ My detailed knowledge system is temporarily unavailable, but I'm still here to help with tracking and basic info! 🚀",
            "Interesting question about '" + user_input + "'! 🌟 While my advanced responses are temporarily offline, I can still help you explore this satellite tracker and find amazing space objects! 🛰️",
            "I'd love to give you detailed info about '" + user_input + "'! 🚀 My knowledge database is having temporary issues, but you can still use this tracker to explore satellites in real-time! 🌍"
        ]

        return random.choice(fallback_responses)

    except Exception as e:
        print("ENHANCED Error: " + str(e))
        return "I'm here to help with satellite tracking! 🛰️ Something went wrong, but I'm still ready to assist you with exploring satellites and space objects. Try asking about the ISS or satellite tracking! 🚀"

print("Enhanced chat system ready! ⚡ Smart responses with Gemini API + fast local fallbacks.")