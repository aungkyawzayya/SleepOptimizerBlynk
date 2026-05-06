import os
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
import socket

logger = logging.getLogger(__name__)

# Use the global blynk.cloud to ensure regional routing works for New Zealand
BLYNK_AUTH = os.getenv("BLYNK_AUTH_TOKEN", "").strip()
BLYNK_SERVER = os.getenv("BLYNK_SERVER", "blynk.cloud").strip()
BLYNK_BASE_URL = f"https://{BLYNK_SERVER}/external/api"

PINS = {
    "temperature": 0, "humidity": 1, "co2": 2, "sound": 3,
    "light": 4, "dust": 5, "motion": 6, "sleep_score": 8,
    "ai_advice": 9, "morning_rpt": 10, "sleep_status": 11, "power": 12,
    "interval": 13, "morning_trigger": 14, "data_source": 15, "room_check_trigger": 16,
    "reset_trigger": 17, "morning_summary": 18, "morning_tips": 19,
    "fan_manual": 24,
    "fan_status": 25,
}

def _has_auth() -> bool:
    return bool(BLYNK_AUTH)

def check_connection() -> bool:
    if not _has_auth(): 
        logger.warning("[BLYNK] No Auth Token found in environment.")
        return False
    url = f"{BLYNK_BASE_URL}/isHardwareConnected?token={BLYNK_AUTH}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read().decode().strip().lower()
            return body == "true"
    except Exception as e:
        logger.error(f"[BLYNK] check_connection error: {e}")
        return False

def update_pin(pin: int, value) -> bool:
    if not _has_auth() or value is None: return False
    url = f"{BLYNK_BASE_URL}/update?token={BLYNK_AUTH}&V{pin}={urllib.parse.quote(str(value))}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return True
    except Exception as e:
        logger.error(f"[BLYNK] update_pin(V{pin}) error: {e}")
        return False

def get_pin(pin: int):
    if not _has_auth(): return None
    url = f"{BLYNK_BASE_URL}/get?token={BLYNK_AUTH}&V{pin}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data[0] if isinstance(data, list) else data
    except Exception as e:
        logger.error(f"[BLYNK] get_pin(V{pin}) error: {e}")
        return None