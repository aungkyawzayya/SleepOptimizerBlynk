"""
Sleep Optimizer — Blynk HTTPS API Client
==========================================
Handles all communication with Blynk Cloud via HTTPS API.
"""

import os
import urllib.request
import urllib.parse


BLYNK_AUTH = os.getenv("BLYNK_AUTH_TOKEN", "")
BLYNK_SERVER = os.getenv("BLYNK_SERVER", "ny3.blynk.cloud")
BLYNK_BASE_URL = f"https://{BLYNK_SERVER}/external/api"

# ── Virtual Pin Mapping ─────────────────────────────────────
PINS = {
    'temperature': 0,   # V0
    'humidity':    1,   # V1
    'co2':         2,   # V2
    'sound':       3,   # V3
    'light':       4,   # V4
    'dust':        5,   # V5
    'motion':      6,   # V6
    'body_temp':   7,   # V7 (reserved)
    'sleep_score': 8,   # V8
    'ai_advice':   9,   # V9
    'morning_rpt': 10,  # V10
}


def update_pin(pin: int, value):
    """Update a single Blynk virtual pin."""
    url = f"{BLYNK_BASE_URL}/update?token={BLYNK_AUTH}&V{pin}={urllib.parse.quote(str(value))}"
    try:
        urllib.request.urlopen(url, timeout=5)
        return True
    except Exception as e:
        print(f"  Blynk write error V{pin}: {e}")
        return False


def update_pins(pin_values: dict):
    """Update multiple pins — one request per pin."""
    success = True
    for pin, value in pin_values.items():
        if not update_pin(pin, value):
            success = False
    return success


def send_sensor_data(data: dict):
    """Send sensor data dict to Blynk using pin mapping."""
    pin_values = {}
    for key, pin in PINS.items():
        if key in data:
            pin_values[pin] = data[key]
    return update_pins(pin_values)


def update_property(pin: int, prop: str, value: str):
    """Update a widget property (e.g., color)."""
    params = {"token": BLYNK_AUTH, "pin": f"V{pin}", prop: value}
    url = f"{BLYNK_BASE_URL}/update/property?{urllib.parse.urlencode(params)}"
    try:
        urllib.request.urlopen(url, timeout=5)
    except Exception:
        pass


def check_connection():
    """Check if Blynk API is reachable."""
    url = f"{BLYNK_BASE_URL}/isHardwareConnected?token={BLYNK_AUTH}"
    try:
        r = urllib.request.urlopen(url, timeout=5)
        return r.status == 200
    except Exception:
        return False
