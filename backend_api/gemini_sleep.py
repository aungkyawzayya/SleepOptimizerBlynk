"""
Sleep Optimizer — Gemini AI (Sprint 5 Synchronized)
===================================================
Updates: 
- Sound: 0-100 scale (Silent to Loud)
- Light: 0-255 scale (0=Dark, 255=Bright)
- Dust: mg/m³ scale
- Motion: Binary 1/0 integration for room check and morning report
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# -- Config --
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash" 
client = None

def init_gemini():
    global client
    if not GEMINI_API_KEY:
        print("  WARNING: GEMINI_API_KEY not set")
        return False
    client = genai.Client(api_key=GEMINI_API_KEY)
    print(f"  Gemini AI: {GEMINI_MODEL} initialized")
    return True

def is_available():
    return client is not None

def _extract_text(response) -> str:
    """Safely extract text from Gemini response."""
    try:
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        return response.text
    except Exception as e:
        logger.error(f"[GEMINI PARSE ERROR] {e}")
        return ""

def _format_sensor(data: dict) -> str:
    """Format sensor data including the binary motion state."""
    labels = {
        'temperature': 'Temperature: {v}°C',
        'sound': 'Sound Level: {v}/100 (0=Silent, 100=Very Loud)',
        'light': 'Light Level: {v}/255 (0=Total Darkness, 255=Bright)',
        'dust': 'Dust Density: {v} mg/m³',
        'motion': 'Motion Detected: {"Yes" if v==1 else "No"}'
    }
    lines = []
    for key, fmt in labels.items():
        if key in data and data[key] is not None:
            lines.append(fmt.format(v=data[key]))
    return '\n'.join(lines)

# ══════════════════════════════════════════════════════════════
# 1. ROOM CHECK — Updated for 5 Sensors
# ══════════════════════════════════════════════════════════════
def room_check(sensor_data: dict) -> Optional[dict]:
    if not is_available():
        return None

    prompt = f"""You are a sleep environment analyzer for an IoT bedroom monitor.

Current sensor readings:
{_format_sensor(sensor_data)}
Time: {datetime.now().strftime("%H:%M")}

Analyze the bedroom conditions and respond in this exact JSON format:
{{"score": <integer 0-100>, "advice": "<one sentence advice, max 80 chars>"}}

Updated Scoring Guide for this hardware:
- Temperature: Ideal 18-22°C.
- Sound: Scale 0-100. Ideal is below 15 (Silent). 
- Light: Scale 0-255. Ideal is 0-5 (Pitch black).
- Dust: Ideal below 0.035 mg/m³.
- Motion: 1=Motion Detected, 0=Still. Nighttime movement lowers the score.

Only score sensors that have readings. 100 = perfect sleep conditions.
Respond with ONLY the JSON, no other text."""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        text = _extract_text(response)
        return json.loads(text)
    except Exception as e:
        logger.error(f"[GEMINI ROOM CHECK ERROR] {e}")
        return None

# ══════════════════════════════════════════════════════════════
# 2. MORNING REPORT — Calculates Restlessness
# ══════════════════════════════════════════════════════════════
def morning_report(history: list) -> Optional[dict]:
    if not is_available():
        return None

    total_readings = len(history)
    if total_readings == 0:
        return None

    # Calculate motion frequency (restlessness)
    motion_events = sum(1 for data in history if data.get('motion', 0) == 1)
    restlessness = round((motion_events / total_readings) * 100, 1)

    prompt = f"""You are a sleep analyst. 
Review this overnight sensor history:
{history}

Summary Stats:
- Total readings taken: {total_readings}
- Motion detected {motion_events} times ({restlessness}% of the night).

Analyze the data based on these hardware scales:
- Temp: Ideal 18-22°C
- Light: 0 (Dark) to 255 (Bright)
- Sound: 0 (Silent) to 100 (Loud)
- Dust: Ideal < 0.035 mg/m³
- Motion: Frequent movement indicates restless sleep.

Provide your response in EXACTLY this JSON format:
{{"score": <0-100>, "summary": "<max 250 chars>", "tips": "<max 250 chars>"}}"""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                response_mime_type="application/json"
            )
        )
        text = _extract_text(response)
        return json.loads(text)
    except Exception as e:
        logger.error(f"[GEMINI MORNING REPORT ERROR] {e}")
        return None