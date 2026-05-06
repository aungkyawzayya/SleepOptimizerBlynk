import os
import json
import logging
import urllib.request
import urllib.parse
import urllib.error

logger = logging.getLogger(__name__)

# Core Config - Pulls from your .env file
BLYNK_AUTH = os.getenv("BLYNK_AUTH_TOKEN", "").strip()
BLYNK_SERVER = os.getenv("BLYNK_SERVER", "blynk.cloud").strip()
BLYNK_BASE_URL = f"https://{BLYNK_SERVER}/external/api"

# Pin Mapping - Matches your Blynk Template
PINS = {
    "temperature": 0, "humidity": 1, "sound": 3, "light": 4, 
    "motion": 6, "fan_manual": 24, "fan_status": 25
}

def check_connection() -> bool:
    """Validates if the Auth Token is accepted by the Blynk Cloud."""
    if not BLYNK_AUTH: return False
    # We test the token by attempting to GET a value from a standard pin
    url = f"{BLYNK_BASE_URL}/get?token={BLYNK_AUTH}&V13"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.getcode() == 200
    except Exception as e:
        logger.error(f"[BLYNK] Connection test failed: {e}")
        return False

def update_pin(pin: int, value) -> bool:
    """Pushes a value to a specific Virtual Pin."""
    if not BLYNK_AUTH or value is None: return False
    url = f"{BLYNK_BASE_URL}/update?token={BLYNK_AUTH}&V{pin}={urllib.parse.quote(str(value))}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return True
    except Exception as e:
        logger.error(f"[BLYNK] Failed to update V{pin}: {e}")
        return False

def get_pin(pin: int):
    """Retrieves a value from a specific Virtual Pin."""
    if not BLYNK_AUTH: return None
    url = f"{BLYNK_BASE_URL}/get?token={BLYNK_AUTH}&V{pin}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data[0] if isinstance(data, list) else data
    except Exception as e:
        logger.error(f"[BLYNK] Failed to get V{pin}: {e}")
        return None