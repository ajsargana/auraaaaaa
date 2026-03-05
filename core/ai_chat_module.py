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

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent action: satellite name → (canonical TLE search term, confirmation msg)
# ---------------------------------------------------------------------------
_SAT_SHORTCUTS = [
    (r'\biss\b|\binternational\s+space\s+station\b',
     'ISS', 'Focusing on the International Space Station!'),
    (r'\bstarlink\b',
     'STARLINK', 'Searching for Starlink satellites!'),
    (r'\bhubble\b',
     'HUBBLE SPACE TELESCOPE', 'Focusing on the Hubble Space Telescope!'),
    (r'\bjwst\b|\bjames\s+webb\b|\bwebb\s+telescope\b',
     'JWST', 'Selecting the James Webb Space Telescope!'),
    (r'\btiangong\b',
     'TIANGONG', 'Selecting Tiangong Space Station!'),
    (r'\bgoes[\s\-]?\d*\b',
     'GOES', 'Selecting GOES weather satellite!'),
    (r'\bnoaa[\s\-]?\d+\b',
     'NOAA', 'Selecting NOAA weather satellite!'),
    (r'\blandsat[\s\-]?\d?\b',
     'LANDSAT', 'Selecting Landsat Earth observation satellite!'),
    (r'\bsentinel[\s\-]?\d?\b',
     'SENTINEL', 'Selecting Sentinel satellite!'),
    (r'\bterra\b',
     'TERRA', 'Selecting Terra/MODIS satellite!'),
    (r'\baqua\b',
     'AQUA', 'Selecting Aqua/MODIS satellite!'),
    (r'\bgps\b|\bnavstar\b',
     'GPS', 'Selecting GPS constellation satellites!'),
    (r'\bchandra\b',
     'CHANDRA', 'Selecting the Chandra X-ray Observatory!'),
    (r'\bsuomi\b|\bviirs\b',
     'SUOMI NPP', 'Selecting Suomi NPP/VIIRS satellite!'),
    (r'\bbeidou\b|\bcompass\b',
     'BEIDOU', 'Selecting BeiDou navigation satellite!'),
    (r'\bgalileo\b',
     'GALILEO', 'Selecting Galileo navigation satellite!'),
    (r'\bglonass\b',
     'GLONASS', 'Selecting GLONASS navigation satellite!'),
    (r'\biridium\b',
     'IRIDIUM', 'Selecting Iridium satellite!'),
    (r'\bintelsat\b',
     'INTELSAT', 'Selecting Intelsat satellite!'),
    (r'\boneWeb\b|\boneweb\b',
     'ONEWEB', 'Selecting OneWeb satellite!'),
]

# Words that signal the user wants a UI action rather than an explanation
_ACTION_TRIGGER = re.compile(
    r'\b(show|find|select|track|focus|go\s+to|fly\s+to|where\s+is|'
    r'locate|display|highlight|zoom|center|point\s+to|bring\s+up|'
    r'pull\s+up|open|view|see|watch|follow)\b',
    re.IGNORECASE,
)

# Words that confirm a previous suggestion ("show me", "yes", "do it", "ok")
_CONFIRM_TRIGGER = re.compile(
    r'^\s*(show\s+me|yes|yeah|yep|sure|ok|okay|do\s+it|go|'
    r'please|alright|correct|exactly|that\s+one|do\s+that)\s*[!.]?\s*$',
    re.IGNORECASE,
)


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
            'max_tokens': 300,
            'retry_attempts': 2
        }
        self.rate_tracker = {
            'requests_made': 0,
            'window_start': time.time(),
            'is_available': True,
            'last_reset': time.time()
        }

        # Agent system prompt – MUST return JSON so executeAgentAction fires
        self._agent_system_prompt = """You are an AI Agent controlling a 3D satellite tracking app called AURA-AI.

CRITICAL: You MUST respond with ONLY a valid JSON object — no text outside it, no markdown, no code fences.

Choose one action:

1. Select / show / track a satellite:
{"action": "select_satellite", "satellite_name": "<name as it appears in TLE data>", "message": "<one-sentence confirmation>"}

2. Fly camera to a geographic location (when user names a city/country):
{"action": "focus_camera", "lat": <float>, "lon": <float>, "message": "<one-sentence confirmation>"}

3. Answer an informational question (no UI control needed):
{"action": "show_info", "message": "<answer, max 80 words>"}

Satellite names in the database: ISS, STARLINK-*, HUBBLE SPACE TELESCOPE, TIANGONG, GOES-*, NOAA-*, LANDSAT 8, LANDSAT 9, SENTINEL-1A, SENTINEL-2A, GPS IIF-*, TERRA, AQUA, and 950+ others.

ONLY output the JSON object. Nothing else."""

        # Kepler system prompt – informational plain text
        self._kepler_system_prompt = """You are Kepler, a knowledgeable satellite and space mission expert.

Provide detailed, accurate information about satellites, space missions, orbital mechanics, and space agencies.
You have knowledge of 995+ satellites including ISS, Starlink, GPS, weather satellites, Earth observation satellites, and scientific missions.

Keep responses informative but conversational, under 200 words.
DO NOT include any JSON formatting, code blocks, or special markup.
Just provide a natural, informative answer."""

    def set_satellite_database(self, database):
        """Set the satellite database reference"""
        self.satellite_database = database

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_message(self, user_input, chat_type='agent'):
        """Process user message and return appropriate response."""
        try:
            if chat_type == 'agent':
                # ── Fast local path for agent ──────────────────────────────
                local = self._resolve_agent_action(user_input)
                if local:
                    self._add_to_conversation_history(user_input, local)
                    return local

            # Check rate limit before hitting Gemini
            if not self._check_rate_limit():
                fallback = self._create_fallback_response(user_input, chat_type)
                self._add_to_conversation_history(user_input, fallback)
                return fallback

            context = self._get_conversation_context()
            response = self._try_gemini_api(user_input, context, chat_type)

            if response:
                self._add_to_conversation_history(user_input, response)
                return response

            fallback = self._create_fallback_response(user_input, chat_type)
            self._add_to_conversation_history(user_input, fallback)
            return fallback

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            if chat_type == 'agent':
                return self._create_response('show_info',
                    "I'm having a technical issue. Try 'show ISS' or 'find Starlink'!")
            return "I'm experiencing some technical difficulties. Please try again!"

    # ------------------------------------------------------------------
    # Local agent action resolver (no API call needed)
    # ------------------------------------------------------------------

    def _resolve_agent_action(self, user_input: str) -> str | None:
        """
        Try to resolve the user's intent locally as a JSON agent action.
        Returns a JSON string ready for the frontend, or None to fall through.
        """
        low = user_input.lower().strip()

        # ── Greetings ──────────────────────────────────────────────────
        if re.match(r'^(hi|hello|hey|hiya|howdy)[\s!.]*$', low):
            return self._create_response('show_info',
                "Hello! I'm your AURA-AI AI Agent. I can select satellites, "
                "fly the camera to any location, and answer space questions. "
                "Try: 'show ISS', 'find Starlink', or 'where is Hubble'!")

        if re.match(r'^(thanks?|thx|thank you)[\s!.]*$', low):
            return self._create_response('show_info', "You're welcome! What else can I show you?")

        if re.match(r'^(bye|goodbye|see you|cya)[\s!.]*$', low):
            return self._create_response('show_info', "Goodbye! Happy satellite tracking!")

        # ── Confirmation ("SHOW ME", "YES", "DO IT") after prior suggestion ─
        if _CONFIRM_TRIGGER.match(low):
            last_sat = self._last_suggested_satellite()
            if last_sat:
                return self._create_response('select_satellite',
                    f'Selecting {last_sat} now!',
                    {'satellite_name': last_sat})

        # ── Direct satellite action ─────────────────────────────────────
        has_action = bool(_ACTION_TRIGGER.search(low))

        for pattern, name, msg in _SAT_SHORTCUTS:
            if re.search(pattern, low, re.IGNORECASE):
                # Accept if there's an action word, OR if the satellite name
                # is basically the whole query (e.g. "ISS", "Hubble?")
                if has_action or len(low.split()) <= 3:
                    return self._create_response('select_satellite', msg,
                                                 {'satellite_name': name})

        # ── "How many satellites" ───────────────────────────────────────
        if re.search(r'\b(how\s+many|count|number\s+of)\b.*\bsat', low):
            count = 0
            if self.satellite_database:
                try:
                    count = len(self.satellite_database.get_satellite_data())
                except Exception:
                    pass
            n = count if count else "950+"
            return self._create_response('show_info',
                f"AURA-AI is currently tracking {n} satellites, including "
                f"communication, navigation, weather, Earth observation, and "
                f"scientific missions from agencies worldwide.")

        # ── What can you do? ───────────────────────────────────────────
        if re.search(r'\b(what\s+can\s+you|help|capabilities|commands)\b', low):
            return self._create_response('show_info',
                "I can: select & track satellites ('show ISS', 'track Hubble'), "
                "fly the camera to locations ('go to London'), filter by type "
                "('show weather satellites'), and answer space questions. "
                "Just tell me what you want to see!")

        return None  # fall through to Gemini

    def _last_suggested_satellite(self) -> str | None:
        """Scan recent history for the last satellite name suggested."""
        for exchange in reversed(self.conversation_history[-5:]):
            ai_resp = exchange.get('ai', '')
            try:
                obj = json.loads(ai_resp)
                if obj.get('satellite_name'):
                    return obj['satellite_name']
                # Also scan message text for satellite names
                msg = obj.get('message', '')
            except (json.JSONDecodeError, TypeError):
                msg = ai_resp
            for _, name, _ in _SAT_SHORTCUTS:
                # Check if the satellite name appears in the message
                if name.split()[0].lower() in msg.lower():
                    return name
        return None

    # ------------------------------------------------------------------
    # Standardised response builder
    # ------------------------------------------------------------------

    def _create_response(self, action: str, message: str, extra_data: dict = None) -> str:
        """Return a JSON string for executeAgentAction."""
        payload = {'action': action, 'message': message}
        if extra_data:
            payload.update(extra_data)
        return json.dumps(payload)

    # ------------------------------------------------------------------
    # Fallback (Gemini unavailable)
    # ------------------------------------------------------------------

    def _create_fallback_response(self, user_input: str, chat_type='agent') -> str:
        low = user_input.lower()

        if chat_type == 'kepler':
            # Kepler: plain informational text
            if any(k in low for k in ['iss', 'international space station']):
                return ("The International Space Station orbits at ~408 km altitude, "
                        "completing 15.5 orbits per day at 27,600 km/h. It's a joint "
                        "project between NASA, Roscosmos, ESA, JAXA, and CSA serving "
                        "as a microgravity research laboratory.")
            if any(k in low for k in ['starlink', 'spacex']):
                return ("Starlink is SpaceX's mega-constellation in LEO at 340–1,200 km. "
                        "Each satellite uses Ka/Ku-band phased-array antennas to deliver "
                        "low-latency broadband internet globally.")
            if any(k in low for k in ['gps', 'navigation']):
                return ("GPS consists of 31 satellites in MEO at 20,200 km. They broadcast "
                        "L1/L2 signals; receivers need 4+ satellites for 3D positioning "
                        "via trilateration.")
            if any(k in low for k in ['weather', 'noaa', 'goes']):
                return ("NOAA's GOES-16/17/18 operate in GEO at 35,786 km, carrying the "
                        "Advanced Baseline Imager (16 spectral bands) and the Geostationary "
                        "Lightning Mapper for storm detection.")
            if any(k in low for k in ['hubble', 'telescope']):
                return ("Hubble orbits at 547 km, carrying a 2.4-m primary mirror. Its "
                        "instruments — WFC3, COS, ACS — have produced 1.5 million+ "
                        "observations, discovering the universe's accelerating expansion.")
            return random.choice([
                "I'm Kepler — ask me about any satellite's specs, mission, or orbit!",
                "As your space expert I can explain orbital mechanics, satellite specs, "
                "and mission objectives. What would you like to know?",
            ])

        # Agent: MUST return JSON actions
        for pattern, name, msg in _SAT_SHORTCUTS:
            if re.search(pattern, low, re.IGNORECASE):
                return self._create_response('select_satellite', msg,
                                             {'satellite_name': name})

        if any(k in low for k in ['show', 'find', 'select', 'track', 'where', 'locate']):
            return self._create_response('show_info',
                "I can select satellites, fly to locations, and answer space questions. "
                "Try: 'show ISS', 'find Hubble', 'focus on Tokyo', or "
                "'where is Landsat'!")

        return self._create_response('show_info',
            "I'm your AURA-AI AI Agent! I can select satellites, fly the camera to "
            "any location, and answer space questions. What would you like to explore?")

    # ------------------------------------------------------------------
    # Gemini API
    # ------------------------------------------------------------------

    def _try_gemini_api(self, user_input: str, context: str = '', chat_type='agent') -> str | None:
        """Call Gemini and return the response string, or None on failure."""
        try:
            self.rate_tracker['requests_made'] += 1

            system_prompt = (self._agent_system_prompt
                             if chat_type == 'agent'
                             else self._kepler_system_prompt)

            full_prompt = f"{system_prompt}\n\n{context}\nUser: {user_input}\nAI:"

            request_data = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {
                    "temperature": 0.4 if chat_type == 'agent' else 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": self.gemini_config['max_tokens'],
                },
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH",        "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",  "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT",  "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ],
            }

            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': self.gemini_config['api_key'],
            }

            response = requests.post(
                self.gemini_config['endpoint'],
                json=request_data,
                headers=headers,
                timeout=self.gemini_config['timeout'],
            )

            if response.status_code != 200:
                logger.warning(f"Gemini API error {response.status_code}: {response.text[:200]}")
                return None

            data = response.json()
            candidates = data.get('candidates', [])
            if not candidates:
                return None
            parts = candidates[0].get('content', {}).get('parts', [])
            if not parts:
                return None

            ai_text = parts[0].get('text', '').strip()
            if not ai_text:
                return None

            # ── For agent tab: ensure we return valid JSON ─────────────
            if chat_type == 'agent':
                # Strip markdown code fences if Gemini added them
                ai_text = re.sub(r'^```(?:json)?\s*', '', ai_text, flags=re.MULTILINE)
                ai_text = re.sub(r'```\s*$', '', ai_text, flags=re.MULTILINE).strip()
                try:
                    obj = json.loads(ai_text)
                    # Validate it has the required 'action' key
                    if 'action' not in obj:
                        obj = {'action': 'show_info', 'message': ai_text}
                    return json.dumps(obj)
                except (json.JSONDecodeError, ValueError):
                    # Gemini returned plain text despite instructions – wrap it
                    return self._create_response('show_info', ai_text[:300])

            logger.info(f"Gemini response received for {chat_type}")
            return ai_text

        except requests.exceptions.Timeout:
            logger.warning("Gemini API timed out")
            return None
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None

    # ------------------------------------------------------------------
    # Satellite DB helpers
    # ------------------------------------------------------------------

    def _search_satellites_in_db(self, query: str) -> list:
        if not self.satellite_database:
            return []
        try:
            satellites = self.satellite_database.get_satellite_data()
            q = query.lower().strip()
            scored = []
            for sat in satellites:
                n = sat['name'].lower()
                if q == n:               score = 100
                elif q in n:             score = 80
                elif n.startswith(q):    score = 70
                elif all(w in n for w in q.split()): score = 60
                elif any(w in n for w in q.split() if len(w) > 2): score = 40
                else:                    continue
                scored.append((score, sat))
            scored.sort(key=lambda x: -x[0])
            return [s for _, s in scored[:15]]
        except Exception as e:
            logger.error(f"Error searching satellites: {e}")
            return []

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def _check_rate_limit(self) -> bool:
        now = time.time()
        if now - self.rate_tracker['window_start'] >= 60:
            self.rate_tracker['requests_made'] = 0
            self.rate_tracker['window_start'] = now
            self.rate_tracker['is_available'] = True
        if self.rate_tracker['requests_made'] >= self.gemini_config['rate_limit']:
            self.rate_tracker['is_available'] = False
            return False
        return True

    # ------------------------------------------------------------------
    # Conversation history
    # ------------------------------------------------------------------

    def _add_to_conversation_history(self, user_input: str, ai_response: str):
        if len(self.conversation_history) >= 10:
            self.conversation_history.pop(0)
        self.conversation_history.append({
            'user': user_input,
            'ai': ai_response,
            'timestamp': time.time(),
        })

    def _get_conversation_context(self) -> str:
        if not self.conversation_history:
            return ""
        lines = ["Recent conversation:"]
        for ex in self.conversation_history[-3:]:
            lines.append(f"User: {ex['user']}")
            # For agent: show only the message field so context is readable
            ai = ex['ai']
            try:
                obj = json.loads(ai)
                ai = obj.get('message', ai)
            except (json.JSONDecodeError, TypeError):
                pass
            lines.append(f"AI: {ai}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level singleton + public API
# ---------------------------------------------------------------------------

ai_assistant = AIAssistant()


def initialize_ai_system(satellite_database):
    global ai_assistant
    ai_assistant.set_satellite_database(satellite_database)
    logger.info("AI chat system initialised with satellite database")


def process_chat_message(user_input: str, chat_type='agent') -> str:
    global ai_assistant
    return ai_assistant.process_message(user_input, chat_type)


# Legacy compatibility
def chat_with_llm(user_input):
    return process_chat_message(user_input)

def set_satellite_database(database):
    initialize_ai_system(database)


__all__ = [
    'AIAssistant', 'ai_assistant',
    'initialize_ai_system', 'process_chat_message',
    'chat_with_llm', 'set_satellite_database',
]
