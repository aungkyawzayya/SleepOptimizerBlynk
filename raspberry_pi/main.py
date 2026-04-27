#!/usr/bin/env python3
import time
import json
import logging
import urllib.request
import urllib.error
import os

# --- SENSOR IMPORTS ---
try:
    from sensors.temperature import read_temperature, setup_temperature
    from sensors.sound import read_sound, setup_sound
    from sensors.dust import read_dust, setup_dust
    from sensors.light import read_light, setup_light
except ImportError:
    print("Warning: Sensor modules not found. Using dummy values.")
    def read_temperature(): return 25.0
    def setup_temperature(): return True
    def read_sound(): return 10.0
    def setup_sound(): return True
    def read_dust(): return 0.02 
    def setup_dust(): return True 
    def read_light(): return 180.0
    def setup_light(): return True

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
API_URL = os.getenv("API_URL", "http://136.119.125.251") 
DATA_ENDPOINT     = f"{API_URL}/sensors/data"
SETTINGS_ENDPOINT = f"{API_URL}/settings"
DEFAULT_INTERVAL  = 5   
SETTINGS_REFRESH  = 5   

def get_settings():
    """Fetch power and interval settings from the VM API"""
    try:
        req = urllib.request.Request(SETTINGS_ENDPOINT, method="GET")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        logger.error(f"Settings fetch error: {e} — using defaults")
        return {"power": 1, "interval": DEFAULT_INTERVAL}

def get_all_sensor_payload():
    """Collects and packages all sensor data"""
    temp = read_temperature()
    dust_val = read_dust()
    sound_val = read_sound()
    light_val = read_light()
    
    return {
        "temperature": round(temp, 2) if temp is not None else 0.0,
        "humidity": 55.0,  
        "dust": dust_val,
        "sound": sound_val,
        "co2": 450,
        "light": light_val,
        "motion": 0
    }

def send_to_fastapi(payload):
    """Sends the JSON payload to the Cloud VM"""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            DATA_ENDPOINT,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"Connection Error: {e}")
        return None

def main():
    logger.info("--- Raspberry Pi Sensor Collector Started ---")
    
    # Initialize Hardware
    setup_temperature()
    setup_sound()
    setup_dust()
    setup_light()

    loop_count = 0
    interval   = DEFAULT_INTERVAL
    power      = 1

    while True:
        try:
            if loop_count % SETTINGS_REFRESH == 0:
                settings = get_settings()
                power    = settings.get("power", 1)
                interval = settings.get("interval", DEFAULT_INTERVAL)

            if not power:
                logger.info(f"[{time.strftime('%H:%M:%S')}] System OFF — idling...")
                time.sleep(interval)
                loop_count += 1
                continue

            # 1. Collect Data
            payload = get_all_sensor_payload()
            
            # 2. Send to Cloud
            result  = send_to_fastapi(payload)

            # 3. Display Detailed Result in Terminal
            if result:
                timestamp = time.strftime('%H:%M:%S')
                status = result.get('status', 'success')
                # Updated log line to include Sound
                logger.info(
                    f"[{timestamp}] Sent: {payload['temperature']}°C | "
                    f"Sound: {payload['sound']} | "
                    f"Dust: {payload['dust']} mg/m³ | "
                    f"Light: {payload['light']} | "
                    f"Status: {status}"
                )
            else:
                logger.warning(f"[{time.strftime('%H:%M:%S')}] Server unreachable.")

        except Exception as e:
            logger.error(f"Loop Error: {e}")

        loop_count += 1
        time.sleep(interval)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Collector Stopped by User.")