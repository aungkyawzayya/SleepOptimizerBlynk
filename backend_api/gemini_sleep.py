"""
Sleep Optimizer — Gemini AI
=============================
Two AI functions:
  1. room_check()    → Sleep score (0-100) + short advice
  2. morning_report() → Night summary + score + tips for tonight
"""

import os
import json
from datetime import datetime
from typing import Optional

from google import genai
from google.genai import types


# ── Config ──────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"
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


def _extract_text(response) -> Optional[str]:
    """Safely extract text from Gemini response."""
    try:
        if response.text:
            return response.text.strip()
    except Exception:
        pass
    try:
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, 'text') and part.text:
                    return part.text.strip()
    except Exception:
        pass
    return None


def _format_sensor(data: dict) -> str:
    """Format sensor data for prompt."""
    labels = {
        'temperature': 'Temperature: {v}°C',
        'humidity': 'Humidity: {v}%',
        'co2': 'CO₂: {v} ppm',
        'sound': 'Sound: {v} dB',
        'light': 'Light: {v} lux',
        'dust': 'Dust PM2.5: {v} µg/m³',
        'motion': 'Motion: {v}',
    }
    lines = []
    for key, fmt in labels.items():
        if key in data and data[key] is not None:
            lines.append(fmt.format(v=data[key]))
    return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════
# 1. ROOM CHECK — Score + Advice
# ══════════════════════════════════════════════════════════════
def room_check(sensor_data: dict) -> Optional[dict]:
    """
    Analyze current sensor readings.
    Returns: {"score": 0-100, "advice": "short text"}
    """
    if not is_available():
        return None

    prompt = f"""You are a sleep environment analyzer for an IoT bedroom monitor.

Current sensor readings:
{_format_sensor(sensor_data)}
Time: {datetime.now().strftime("%H:%M")}

Analyze the bedroom conditions and respond in this exact JSON format:
{{"score": <integer 0-100>, "advice": "<one sentence advice, max 80 chars>"}}

Scoring guide:
- Temperature: Ideal 18-22°C
- Humidity: Ideal 40-60%
- CO₂: Ideal below 800ppm
- Sound: Ideal below 30dB
- Light: Ideal 0 lux for sleep
- Dust PM2.5: Ideal below 12 µg/m³
- Motion: No motion is ideal

Only score sensors that have readings. 100 = perfect sleep conditions.
Respond with ONLY the JSON, no other text."""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=200,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        text = _extract_text(response)
        if not text:
            print("  Gemini room_check: no text in response")
            return None

        # Clean JSON from possible markdown code fences
        text = text.replace('```json', '').replace('```', '').strip()
        result = json.loads(text)

        # Validate
        score = int(result.get('score', 0))
        score = max(0, min(100, score))
        advice = str(result.get('advice', ''))[:120]

        return {"score": score, "advice": advice}

    except Exception as e:
        print(f"  Gemini room_check error: {e}")
        return None


# ══════════════════════════════════════════════════════════════
# 2. MORNING REPORT — Night summary + score + tips
# ══════════════════════════════════════════════════════════════
def morning_report(night_data: list) -> Optional[dict]:
    """
    Generate morning sleep report from overnight data.
    Returns: {"score": 0-100, "summary": "...", "tips": "..."}
    """
    if not is_available():
        return None

    if not night_data:
        return None

    # Format overnight data
    readings = []
    for entry in night_data:
        ts = entry.get('timestamp', '?')
        parts = []
        if 'temperature' in entry:
            parts.append(f"Temp={entry['temperature']}°C")
        if 'humidity' in entry:
            parts.append(f"Hum={entry['humidity']}%")
        if 'co2' in entry:
            parts.append(f"CO₂={entry['co2']}ppm")
        if 'sound' in entry:
            parts.append(f"Sound={entry['sound']}dB")
        if 'light' in entry:
            parts.append(f"Light={entry['light']}lux")
        if 'dust' in entry:
            parts.append(f"Dust={entry['dust']}")
        if 'motion' in entry:
            parts.append(f"Motion={entry['motion']}")
        readings.append(f"{ts}: {', '.join(parts)}")

    data_text = '\n'.join(readings[-20:])  # Last 20 readings max

    prompt = f"""You are a sleep environment analyst for an IoT bedroom monitor.

Overnight sensor data:
{data_text}

Generate a morning sleep report. Respond in this exact JSON format:
{{
  "score": <integer 0-100 overall night score>,
  "summary": "<2-3 sentence summary of overnight conditions>",
  "tips": "<1-2 specific tips for improving sleep tonight>"
}}

Respond with ONLY the JSON, no other text."""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=500,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        text = _extract_text(response)
        if not text:
            print("  Gemini morning_report: no text in response")
            return None

        text = text.replace('```json', '').replace('```', '').strip()
        result = json.loads(text)

        score = int(result.get('score', 0))
        score = max(0, min(100, score))
        summary = str(result.get('summary', ''))
        tips = str(result.get('tips', ''))

        return {"score": score, "summary": summary, "tips": tips}

    except Exception as e:
        print(f"  Gemini morning_report error: {e}")
        return None