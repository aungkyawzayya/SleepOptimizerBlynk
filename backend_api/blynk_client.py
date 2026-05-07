import os
import logging
import requests

logger = logging.getLogger(__name__)

# Retrieve the token securely from the environment
BLYNK_AUTH_TOKEN = os.getenv("BLYNK_AUTH_TOKEN")
BLYNK_BASE_URL = "https://ny3.blynk.cloud/external/api/update"

# --- THE CORRECTED PIN MAP ---
# Mapped exactly to your Blynk Web Console Datastreams
PINS = {
    "temperature": "V0",
    "sound": "V3",
    "light": "V4",
    "dust": "V5",
    "motion": "V6",
    "fan": "V24",      # Fan Power Trigger
    "ai_report": "V9", # AI Advice
    "status": "V11"    # Sleep Status
}

def update_pin(pin, value):
    """
    Sends a single pin update to Blynk using the robust 'requests' library.
    """
    if not BLYNK_AUTH_TOKEN:
        logger.error("CRITICAL: BLYNK_AUTH_TOKEN is missing!")
        return False
        
    url = f"{BLYNK_BASE_URL}?token={BLYNK_AUTH_TOKEN}&{pin}={value}"
    
    try:
        # Using requests handles any background redirects gracefully
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            logger.error(f"[BLYNK] HTTP Error {response.status_code} on {pin}: {response.text}")
            return False
        return True
            
    except Exception as e:
        logger.error(f"[BLYNK] Connection failed for {pin}: {e}")
        return False

def sync_data_to_blynk(sensor_data):
    """
    Takes the incoming gRPC dictionary, matches it to the right pins, 
    and fires the updates to the Blynk dashboard.
    """
    success = False
    
    for key, value in sensor_data.items():
        if key in PINS:
            pin = PINS[key]
            if update_pin(pin, value):
                success = True
                
    if success:
        # This will print the success message you see in your gRPC logs
        logger.info(f"gRPC Data Synced to Blynk: {sensor_data.get('temperature', 'N/A')}C")