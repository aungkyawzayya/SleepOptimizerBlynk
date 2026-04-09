import os
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
import socket

logger = logging.getLogger(__name__)

BLYNK_AUTH = os.getenv("BLYNK_AUTH_TOKEN", "").strip()
BLYNK_SERVER = os.getenv("BLYNK_SERVER", "ny3.blynk.cloud").strip()
BLYNK_BASE_URL = f"https://{BLYNK_SERVER}/external/api"

PINS = {
    "temperature": 0, "humidity": 1, "co2": 2, "sound": 3,
    "light": 4, "dust": 5, "motion": 6, "sleep_status": 7, "sleep_score": 8,
    "ai_advice": 9, "morning_rpt": 10, "interval": 13,
    "power": 12, "morning_trigger": 14, "data_source": 15, "room_check_trigger": 16,
    "reset_trigger": 17,
}

def _has_auth() -> bool:
    return bool(BLYNK_AUTH)

def check_connection() -> bool:
    if not _has_auth(): return False
    url = f"{BLYNK_BASE_URL}/isHardwareConnected?token={BLYNK_AUTH}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read().decode().strip().lower()
            return body == "true"
    except (urllib.error.URLError, socket.timeout) as e:
        logger.error(f"[BLYNK] check_connection error: {e}")
        return False

def get_pin(pin: int):
    if not _has_auth(): return None
    url = f"{BLYNK_BASE_URL}/get?token={BLYNK_AUTH}&V{pin}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data[0] if isinstance(data, list) else data
    except (urllib.error.URLError, socket.timeout, json.JSONDecodeError) as e:
        logger.error(f"[BLYNK] get_pin(V{pin}) error: {e}")
        return None

def update_pin(pin: int, value) -> bool:
    if not _has_auth() or value is None: return False
    url = f"{BLYNK_BASE_URL}/update?token={BLYNK_AUTH}&V{pin}={urllib.parse.quote(str(value))}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return True
    except (urllib.error.URLError, socket.timeout) as e:
        logger.error(f"[BLYNK] update_pin(V{pin}) error: {e}")
        return False

def send_sensor_data(data: dict) -> bool:
    """Maps dictionary keys to Blynk Pins and sends them."""
    success = True
    for key, pin in PINS.items():
        if key in data and data[key] is not None:
            if not update_pin(pin, data[key]):
                success = False
    return success

def update_property(pin: int, prop: str, value: str) -> bool:
    """Updates widget properties like color or label."""
    if not _has_auth(): return False
    params = {"token": BLYNK_AUTH, "pin": f"V{pin}", prop: value}
    url = f"{BLYNK_BASE_URL}/update/property?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return True
    except (urllib.error.URLError, socket.timeout) as e:
        logger.error(f"[BLYNK] update_property(V{pin}, {prop}) error: {e}")
        return False