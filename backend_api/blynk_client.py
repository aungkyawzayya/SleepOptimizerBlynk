import urllib.request
import logging
import os

logger = logging.getLogger(__name__)

# Replace with your actual Blynk Auth Token
BLYNK_AUTH_TOKEN = os.getenv("BLYNK_AUTH_TOKEN", "your_token_here")
BLYNK_URL = "https://sgp1.blynk.cloud/external/api"

# Pin Mapping
PINS = {
    "status": "V0",
    "temperature": "V1",
    "sound": "V2",
    "light": "V3",
    "dust": "V4",
    "motion": "V5",
    "fan": "V6",
    "ai_report": "V7"  # Pin for the AI analysis text
}

def update_pin(pin_name, value):
    try:
        # Clean the pin name to prevent "VV0" errors
        # If 'V0' is passed, clean_pin becomes '0'
        clean_pin = str(pin_name).replace("V", "")
        
        url = f"{BLYNK_URL}/update?token={BLYNK_AUTH_TOKEN}&V{clean_pin}={value}"
        
        # For long strings (AI reports), we must encode the URL
        if isinstance(value, str):
            value_encoded = urllib.parse.quote(value)
            url = f"{BLYNK_URL}/update?token={BLYNK_AUTH_TOKEN}&V{clean_pin}={value_encoded}"

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.getcode() == 200:
                return True
    except Exception as e:
        logger.error(f"[BLYNK] Failed to update V{clean_pin}: {e}")
        return False

def check_connection():
    # Simple check to see if the token is valid
    url = f"{BLYNK_URL}/isHardwareConnected?token={BLYNK_AUTH_TOKEN}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.read().decode() == 'true'
    except:
        return False