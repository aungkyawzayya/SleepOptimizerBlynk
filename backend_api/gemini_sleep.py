"""
Sleep Optimizer — Gemini AI (Sprint 5 Synchronized)
===================================================
Updates: 
- Sound: 0-100 scale (Silent to Loud)
- Light: 0-255 scale (0=Dark, 255=Bright)
- Dust: mg/m³ scale
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
GEMINI_MODEL = "gemini-2.0-flash" # Adjusted to current stable version
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

def _format_sensor(data: dict) -> str:
    """Format sensor data for prompt using your 4-sensor suite standards."""
    labels = {
        'temperature': 'Temperature: {v}°C',
        'sound': 'Sound Level: {v}/100 (0=Silent, 100=Very Loud)',
        'light': 'Light Level: {v}/255 (0=Total Darkness, 255=Bright)',
        'dust': 'Dust Density: {v} mg/m³',
    }
    lines = []
    for key, fmt in labels.items():
        if key in data and data[key] is not None:
            lines.append(fmt.format(v=data[key]))
    return '\n'.join(lines)

# ══════════════════════════════════════════════════════════════
# 1. ROOM CHECK — Updated for 8-bit / Normalized scales
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

Only score sensors that have readings. 100 = perfect sleep conditions.
Respond with ONLY the JSON, no other text."""

    # ... (Keep existing response handling and JSON extraction logic) ...
    # Ensure to use the existing _extract_text and validation from your previous code