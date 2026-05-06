import os
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
import socket
from pathlib import Path
from dotenv import load_dotenv

# --- Critical: Load .env at the module level ---
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

# Core Config
BLYNK_AUTH = os.getenv("BLYNK_AUTH_TOKEN", "").strip()
BLYNK_SERVER = os.getenv("BLYNK_SERVER", "blynk.cloud").strip()
BLYNK_BASE_URL = f"https://{BLYNK_SERVER}/external/api"

# Complete Pin Mapping based on your Sleep Optimizer template
PINS = {
    "temperature": 0, "humidity": 1, "co2": 2, "sound": 3,
    "light": 4, "dust": 5, "motion": 6, "sleep_score": 8,
    "ai_advice": 9, "morning_rpt": 10, "sleep_status": 11, "power": 12,
    "interval": 13, "morning_trigger": 14, 
    "data_source": 15,  # V15 toggle in your dashboard
    "room_check_trigger": 16,
    "reset_trigger": 17, "morning_summary": 18, "morning_tips": 19,
    "fan_manual": 24, "fan_status": 25,
}

def check_connection() -> bool:
    """Validates if the Auth Token is accepted by the Blynk Cloud."""
    if not BLYNK_AUTH: 
        logger.error("[BLYNK] No Auth Token found in environment")
        return False
    
    url = f"{BLYNK_BASE_URL}/isServerAlive?token={BLYNK_AUTH}"
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