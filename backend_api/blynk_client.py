import os
import logging
import requests

logger = logging.getLogger(__name__)

# Load token from .env
BLYNK_AUTH_TOKEN = os.getenv("BLYNK_AUTH_TOKEN")

# Use the global URL. The 'requests' library will automatically follow 
# the 308 Redirect to sgp1 (Singapore) or whichever server you are on.
BLYNK_URL = "https://blynk.cloud/external/api"

# Pin Mapping
PINS = {
    "status": "V0",
    "temperature": "V1",
    "sound": "V2",
    "light": "V3",
    "dust": "V4",
    "motion": "V5",
    "fan": "V6",
    "ai_report": "V7"
}

def update_pin(pin_name, value):
    try:
        # Clean the pin name to prevent "VV0" errors
        clean_pin = str(pin_name).replace("V", "")
        url = f"{BLYNK_URL}/update"
        
        # 'params' dictionary automatically safely encodes long AI strings
        payload = {
            "token": BLYNK_AUTH_TOKEN,
            f"V{clean_pin}": value
        }

        # requests.get automatically follows 308 redirects!
        response = requests.get(url, params=payload, timeout=5)
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"[BLYNK] HTTP Error {response.status_code} on V{clean_pin}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"[BLYNK] Failed to update V{pin_name}: {e}")
        return False

def check_connection():
    url = f"{BLYNK_URL}/isHardwareConnected"
    payload = {"token": BLYNK_AUTH_TOKEN}
    try:
        response = requests.get(url, params=payload, timeout=5)
        return response.text.strip().lower() == 'true'
    except Exception as e:
        logger.error(f"[BLYNK] Connection check failed: {e}")
        return False