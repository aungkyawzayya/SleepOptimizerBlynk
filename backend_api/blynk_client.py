import os
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
import socket

logger = logging.getLogger(__name__)

# Core Config - Pulls from your .env file
# Using blynk.cloud ensures optimal routing for your location in Auckland
BLYNK_AUTH = os.getenv("BLYNK_AUTH_TOKEN", "").strip()
BLYNK_SERVER = os.getenv("BLYNK_SERVER", "blynk.cloud").strip()
BLYNK_BASE_URL = f"https://{BLYNK_SERVER}/external/api"

# Complete Pin Mapping based on your Sleep Optimizer template
PINS = {
    "temperature": 0, 
    "humidity": 1, 
    "co2": 2, 
    "sound": 3,
    "light": 4, 
    "dust": 5, 
    "motion": 6, 
    "sleep_score": 8,
    "ai_advice": 9, 
    "morning_rpt": 10, 
    "sleep_status": 11, 
    "power": 12,
    "interval": 13, 
    "morning_trigger": 14, 
    "data_source": 15,  # Matches V15 toggle in Screenshot 2026-05-06 at 3.51.42 PM.jpg
    "room_check_trigger": 16,
    "reset_trigger": 17, 
    "morning_summary": 18, 
    "morning_tips": 19,
    "fan_manual": 24,
    "fan_status": 25,
}

def _has_auth() -> bool:
    return bool(BLYNK_AUTH)

def check_connection() -> bool:
    """Validates if the Auth Token is accepted by the Blynk Cloud."""
    if not _has_auth(): 
        logger.error("[BLYNK] No Auth Token found in .env")
        return False
    
    # Testing the token by attempting to GET the interval value (V13)
    url = f"{BLYNK_BASE_URL}/get?token={BLYNK_AUTH}&V13"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.getcode() == 200
    except (urllib.error.URLError, socket.timeout) as e:
        logger.error(f"[BLYNK] Connection test failed: {e}")
        return False

def update_pin(pin: int, value) -> bool:
    """Pushes a value to a specific Virtual Pin."""
    if not _has_auth() or value is None: 
        return False
        
    url = f"{BLYNK_BASE_URL}/update?token={BLYNK_AUTH}&V{pin}={urllib.parse.quote(str(value))}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return True
    except (urllib.error.URLError, socket.timeout) as e:
        logger.error(f"[BLYNK] Failed to update V{pin}: {e}")
        return False

def get_pin(pin: int):
    """Retrieves a value from a specific Virtual Pin."""
    if not _has_auth(): 
        return None
        
    url = f"{BLYNK_BASE_URL}/get?token={BLYNK_AUTH}&V{pin}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data[0] if isinstance(data, list) else data
    except (urllib.error.URLError, socket.timeout, json.JSONDecodeError) as e:
        logger.error(f"[BLYNK] Failed to get V{pin}: {e}")
        return None

def send_sensor_data(data: dict) -> bool:
    """Maps dictionary keys to Blynk Pins and sends them."""
    success = True
    for key, pin in PINS.items():
        if key in data and data[key] is not None:
            if not update_pin(pin, data[key]):
                success = False
    return success