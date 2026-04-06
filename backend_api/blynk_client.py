import os
import json
import urllib.request
import urllib.parse

BLYNK_AUTH = os.getenv("BLYNK_AUTH_TOKEN", "").strip()
BLYNK_SERVER = os.getenv("BLYNK_SERVER", "ny3.blynk.cloud").strip()
BLYNK_BASE_URL = f"https://{BLYNK_SERVER}/external/api"

# CRITICAL: main.py needs this dictionary!
PINS = {
    "temperature": 0, "humidity": 1, "co2": 2, "sound": 3,
    "light": 4, "dust": 5, "motion": 6, "sleep_score": 8,
    "ai_advice": 9, "morning_rpt": 10, "interval": 13,
    "power": 12, "morning_trigger": 14, "data_source": 15,
}

def _has_auth() -> bool:
    return bool(BLYNK_AUTH)

def check_connection() -> bool:
    """Check if Blynk API is reachable."""
    if not _has_auth(): return False
    url = f"{BLYNK_BASE_URL}/isHardwareConnected?token={BLYNK_AUTH}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status == 200
    except: return False

def get_pin(pin: int):
    """Read a virtual pin value from Blynk safely."""
    if not _has_auth(): return None
    url = f"{BLYNK_BASE_URL}/get?token={BLYNK_AUTH}&V{pin}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            if isinstance(data, list):
                return data[0] if data else None
            return data
    except Exception as e:
        print(f"[BLYNK] Get V{pin} FAILED: {e}")
        return None

def update_pin(pin: int, value) -> bool:
    """Update one Blynk virtual pin."""
    if not _has_auth() or value is None: return False
    url = f"{BLYNK_BASE_URL}/update?token={BLYNK_AUTH}&V{pin}={urllib.parse.quote(str(value))}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return True
    except: return False