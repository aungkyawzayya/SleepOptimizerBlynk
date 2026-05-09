import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logger = logging.getLogger(__name__)

BLYNK_AUTH_TOKEN = os.getenv("BLYNK_AUTH_TOKEN")
BLYNK_BASE_URL = "https://ny3.blynk.cloud/external/api/update"
BLYNK_GET_URL  = "https://ny3.blynk.cloud/external/api/get"

PINS = {
    "temperature":        "V0",
    "sound":              "V3",
    "light":              "V4",
    "dust":               "V5",
    "motion":             "V6",
    "fan":                "V24",
    "ai_report":          "V9",
    "ai_advice":          "V9",   # alias used by ai_advice.py
    "status":             "V11",
    "room_check_trigger": "V16",  # "CHECK NOW" button
    "morning_trigger":    "V14",  # "Generate Morning Report" button
    "morning_rpt":        "V10",  # Sleep Score (short header)
    "morning_summary":    "V18",  # Sleep Environment Summary
    "morning_tips":       "V19",  # Sleep Quality Improvement Tips
    "sleep_score":        "V8",   # numeric gauge
    "sleep_status":       "V11",  # status banner
    "data_source":        "V15",
    "power":              "V12",
    "interval":           "V13",
    "reset_trigger":      "V17",
}

def update_pin(pin, value):
    """Sends a single pin update to Blynk."""
    if not BLYNK_AUTH_TOKEN:
        logger.error("CRITICAL: BLYNK_AUTH_TOKEN is missing!")
        return False

    url = f"{BLYNK_BASE_URL}?token={BLYNK_AUTH_TOKEN}&{pin}={value}"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            logger.error(f"[BLYNK] HTTP Error {response.status_code} on {pin}: {response.text}")
            return False
        return True
    except Exception as e:
        logger.error(f"[BLYNK] Connection failed for {pin}: {e}")
        return False

def get_pin(pin):
    """Reads a single pin value from Blynk. Returns the raw string value, or None on error."""
    if not BLYNK_AUTH_TOKEN:
        logger.error("CRITICAL: BLYNK_AUTH_TOKEN is missing!")
        return None

    url = f"{BLYNK_GET_URL}?token={BLYNK_AUTH_TOKEN}&{pin}"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            logger.error(f"[BLYNK] HTTP Error {response.status_code} reading {pin}: {response.text}")
            return None
        return response.text.strip()
    except Exception as e:
        logger.error(f"[BLYNK] Connection failed reading {pin}: {e}")
        return None


def sync_data_to_blynk(sensor_data):
    """Maps sensor dict keys to Blynk pins and sends updates."""
    SKIP_KEYS = {"fan"}  # V24 is user control — never overwrite it
    success = False
    for key, value in sensor_data.items():
        if key in PINS and key not in SKIP_KEYS:
            pin = PINS[key]
            if update_pin(pin, value):
                success = True
    if success:
        logger.info(f"gRPC Data Synced to Blynk: {sensor_data.get('temperature', 'N/A')}C")