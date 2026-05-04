"""
Sleep Optimizer — Gemini AI (Sprint 5 Synchronized)
===================================================
Updates: 
- Sound: 0-255 scale (Silent to Loud)
- Light: 0-255 scale (0=Dark, 255=Bright)
- Dust: mg/m³ scale
- Motion: Binary 1/0 integration
- Feature: Sensor Fusion Logic applied to Morning Report
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
    try:
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        return response.text
    except Exception as e:
        logger.error(f"[GEMINI PARSE ERROR] {e}")
        return ""

def _format_sensor(data: dict) -> str:
    labels = {
        'temperature': 'Temperature: {v}°C',
        'sound': 'Sound Level: {v}/255 (0=Silent, 255=Very Loud)',
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
# 1. ROOM CHECK — Real-time Environment Analysis
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
- Sound: Scale 0-255. Ideal is below 40. 
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
# 2. MORNING REPORT — Hybrid (Local Sensor Fusion + AI Text)
# ══════════════════════════════════════════════════════════════
def morning_report(history: list) -> Optional[dict]:
    if not is_available():
        return None

    total_readings = len(history)
    if total_readings == 0:
        return None

    # --- 1. LOCAL DATA AGGREGATION ---
    motion_events = sum(1 for data in history if data.get('motion', 0) == 1)
    avg_motion_percent = (motion_events / total_readings) * 100
    
    avg_sound = sum(data.get('sound', 0) for data in history) / total_readings
    avg_light = sum(data.get('light', 0) for data in history) / total_readings
    avg_dust = sum(data.get('dust', 0) for data in history) / total_readings
    max_sound = max((data.get('sound', 0) for data in history), default=0)

    # --- 2. LOCAL SENSOR FUSION MATH ---
    # Penalty calculation (assuming ideal is 0 for all)
    penalty_motion = avg_motion_percent
    penalty_sound = (avg_sound / 255.0) * 100  
    penalty_light = (avg_light / 255.0) * 100  
    penalty_dust = min((avg_dust / 0.05) * 100, 100) 

    # Weighted Total
    total_penalty = (
        (0.30 * penalty_motion) +
        (0.30 * penalty_sound) +
        (0.25 * penalty_light) +
        (0.15 * penalty_dust)
    )
    
    calculated_score = int(max(0, min(100, 100 - total_penalty)))

    # --- 3. AI TEXT GENERATION ---
    prompt = f"""You are a sleep analyst. 
Review this overnight summary data:
- Final Sleep Score: {calculated_score}/100 
- Restlessness (Motion): {round(avg_motion_percent, 1)}% of the night
- Avg Light: {round(avg_light, 1)}/255
- Max Sound Spike: {max_sound}/255
- Avg Dust: {round(avg_dust, 3)} mg/m³

The Sleep Score was already calculated mathematically using sensor fusion. The motion sensor is highly sensitive, so the score relied heavily on the light and sound data.

Write a short summary and improvement tips for the dashboard based on these numbers.

Provide your response in EXACTLY this JSON format:
{{"score": {calculated_score}, "summary": "<max 250 chars>", "tips": "<max 250 chars>"}}"""

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