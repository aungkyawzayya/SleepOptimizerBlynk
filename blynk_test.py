#!/usr/bin/env python3
"""
Sleep Optimizer — Blynk + Gemini AI (TEST MODE)
=================================================
Uses FAKE SENSORS and Blynk HTTPS API.
Works on any computer (Mac, Windows, Linux).

Virtual Pin Mapping:
  V0-V7: Sensors | V8-V10: AI

Usage:
  1. Create .env with BLYNK_AUTH_TOKEN (and optionally GEMINI_API_KEY)
  2. pip install python-dotenv google-genai
  3. python blynk_test.py
"""

import os
import time
import signal
import sys
import urllib.request
import urllib.parse
from datetime import datetime
from collections import deque

from dotenv import load_dotenv
load_dotenv()

import fake_sensors as sensors

# Try to import Gemini AI module (optional)
try:
    import gemini_sleep
    HAS_AI = True
except ImportError:
    HAS_AI = False


# ── Blynk Config ────────────────────────────────────────────
BLYNK_AUTH = os.getenv("BLYNK_AUTH_TOKEN", "")
BLYNK_SERVER = os.getenv("BLYNK_SERVER", "ny3.blynk.cloud")

if not BLYNK_AUTH:
    print("ERROR: BLYNK_AUTH_TOKEN not set in .env file")
    sys.exit(1)

BLYNK_BASE_URL = f"https://{BLYNK_SERVER}/external/api"

# ── Virtual Pin Constants ───────────────────────────────────
VPIN_TEMPERATURE  = 0
VPIN_HUMIDITY     = 1
VPIN_CO2          = 2
VPIN_SOUND        = 3
VPIN_LIGHT        = 4
VPIN_DUST         = 5
VPIN_MOTION       = 6
VPIN_BODY_TEMP    = 7
VPIN_SLEEP_SCORE  = 8
VPIN_AI_ADVICE    = 9
VPIN_MORNING_RPT  = 10
VPIN_MORNING_TRIGGER = 14
VPIN_ROOM_CHECK_TRIGGER = 16

# ── Timing ──────────────────────────────────────────────────
SENSOR_INTERVAL   = 5
AI_INTERVAL       = 60


# ══════════════════════════════════════════════════════════════
# Blynk HTTPS API Client
# ══════════════════════════════════════════════════════════════
def blynk_update(pin_values: dict):
    """Update pins via Blynk HTTPS API — one request per pin."""
    success = True
    for pin, value in pin_values.items():
        url = f"{BLYNK_BASE_URL}/update?token={BLYNK_AUTH}&V{pin}={urllib.parse.quote(str(value))}"
        try:
            urllib.request.urlopen(url, timeout=5)
        except Exception as e:
            print(f"  Blynk write error V{pin}: {e}")
            success = False
    return success


def blynk_update_property(pin, prop, value):
    """Update a widget property (e.g., color)."""
    params = {"token": BLYNK_AUTH, "pin": f"V{pin}", prop: value}
    url = f"{BLYNK_BASE_URL}/update/property?{urllib.parse.urlencode(params)}"
    try:
        urllib.request.urlopen(url, timeout=5)
    except Exception:
        pass


def blynk_get(pin):
    """Fetch a pin value via Blynk HTTPS API."""
    url = f"{BLYNK_BASE_URL}/get?token={BLYNK_AUTH}&V{pin}"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            val = r.read().decode().strip()
            # Blynk returns ["value"] or "value"
            if val.startswith('['): val = val[1:-1].strip('"')
            return val
    except Exception:
        return None


def blynk_check():
    """Check if Blynk API is reachable."""
    url = f"{BLYNK_BASE_URL}/isHardwareConnected?token={BLYNK_AUTH}"
    try:
        r = urllib.request.urlopen(url, timeout=5)
        return r.status == 200
    except Exception:
        return False


# ── Data History ────────────────────────────────────────────
recent_history = deque(maxlen=10)


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


# ══════════════════════════════════════════════════════════════
# AI Analysis
# ══════════════════════════════════════════════════════════════
def run_ai_analysis(sensor_data):
    if not HAS_AI or not gemini_sleep.is_available():
        return

    print(f"[{timestamp()}] Running AI analysis...")
    ai_pins = {}

    score = gemini_sleep.get_sleep_score(sensor_data)
    if score is not None:
        ai_pins[VPIN_SLEEP_SCORE] = score
        print(f"  Sleep Score: {score}/100")
        if score >= 80:
            blynk_update_property(VPIN_SLEEP_SCORE, 'color', '#4CAF50')
        elif score >= 50:
            blynk_update_property(VPIN_SLEEP_SCORE, 'color', '#FF9800')
        else:
            blynk_update_property(VPIN_SLEEP_SCORE, 'color', '#F44336')

    advice = gemini_sleep.get_sleep_advice(sensor_data)
    if advice is not None:
        ai_pins[VPIN_AI_ADVICE] = advice
        print(f"  AI Advice: {advice}")

    if ai_pins:
        blynk_update(ai_pins)

    alert = gemini_sleep.check_smart_alert(sensor_data, history=list(recent_history))
    if alert is not None:
        print(f"  Smart Alert: {alert}")


# ══════════════════════════════════════════════════════════════
# Main Loop
# ══════════════════════════════════════════════════════════════
def main():
    print("=" * 56)
    print("  Sleep Optimizer — TEST MODE (Fake Sensors)")
    print("  Using Blynk HTTPS API")
    print("=" * 56)
    print(f"  Server: {BLYNK_SERVER}")

    if blynk_check():
        print("  Blynk: API reachable!")
    else:
        print("  Blynk: API not reachable — check token/server")
        sys.exit(1)

    ai_ready = False
    if HAS_AI:
        ai_ready = gemini_sleep.init_gemini()
        if ai_ready:
            print("  AI: Gemini 2.5 Flash enabled")
        else:
            print("  AI: Disabled (no GEMINI_API_KEY)")
    else:
        print("  AI: Module not found (sensors only)")

    print(f"  Sensor Interval: {SENSOR_INTERVAL}s")
    print(f"  AI Interval: {AI_INTERVAL}s")
    print("=" * 56)

    last_sensor_time = 0
    last_ai_time = 0

    try:
        while True:
            current_time = time.time()

            if current_time - last_sensor_time >= SENSOR_INTERVAL:
                last_sensor_time = current_time
                data = sensors.read_all()

                success = blynk_update({
                    VPIN_TEMPERATURE: data['temperature'],
                    VPIN_HUMIDITY:    data['humidity'],
                    VPIN_CO2:         data['co2'],
                    VPIN_SOUND:       data['sound'],
                    VPIN_LIGHT:       data['light'],
                    VPIN_DUST:        data['dust'],
                    VPIN_MOTION:      data['motion'],
                    VPIN_BODY_TEMP:   data['body_temp'],
                })

                entry = {**data, 'timestamp': timestamp()}
                recent_history.append(entry)

                status = "OK" if success else "FAIL"
                print(
                    f"[{timestamp()}] [{status}] "
                    f"Temp:{data['temperature']}°C "
                    f"Hum:{data['humidity']}% "
                    f"CO2:{data['co2']}ppm "
                    f"Sound:{data['sound']}dB "
                    f"Light:{data['light']}lux "
                    f"Dust:{data['dust']} "
                    f"Motion:{data['motion']} "
                    f"Body:{data['body_temp']}°C"
                )

            if ai_ready and current_time - last_ai_time >= AI_INTERVAL:
                last_ai_time = current_time
                data = sensors.read_all()
                run_ai_analysis(data)

            # --- Check for Room Check Button (V16) ---
            if ai_ready and (int(current_time) % 5 == 0): # Check every 5s roughly
                val = blynk_get(VPIN_ROOM_CHECK_TRIGGER)
                if val is not None and int(float(val)) == 1:
                    print(f"[{timestamp()}] Button V16 Triggered!")
                    blynk_update({VPIN_ROOM_CHECK_TRIGGER: 0}) # Reset
                    data = sensors.read_all()
                    run_ai_analysis(data)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nShutting down... Goodbye!")


def signal_handler(sig, frame):
    print("\nShutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    main()