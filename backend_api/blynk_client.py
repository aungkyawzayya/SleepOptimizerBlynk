import os
import logging
import requests

logger = logging.getLogger(__name__)

BLYNK_AUTH_TOKEN = os.getenv("BLYNK_AUTH_TOKEN")
BLYNK_BASE_URL = "https://ny3.blynk.cloud/external/api/update"  # Fixed server

PINS = {
    "temperature": "V0",
    "sound": "V3",
    "light": "V4",
    "dust": "V5",
    "motion": "V6",
    "fan": "V24",
    "ai_report": "V9",
    "status": "V11"
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

def sync_data_to_blynk(sensor_data):
    """Maps sensor dict keys to Blynk pins and sends updates."""
    success = False
    for key, value in sensor_data.items():
        if key in PINS:
            pin = PINS[key]
            if update_pin(pin, value):
                success = True
    if success:
        logger.info(f"gRPC Data Synced to Blynk: {sensor_data.get('temperature', 'N/A')}C")