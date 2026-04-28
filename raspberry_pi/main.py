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
    from sensors.fan import setup_fan, set_fan, cleanup_fan
except ImportError as e:
    print(f"Warning: Some sensor modules not found ({e}). Using dummy values.")

    def setup_temperature(): return True
    def read_temperature(): return 25.0
    def setup_sound(): return True
    def read_sound(): return 0.0
    def setup_dust(): return True
    def read_dust(): return 0.02
    def setup_light(): return True
    def read_light(): return 180
    def setup_fan(): return True
    def set_fan(state): print(f"Dummy fan state: {state}")
    def cleanup_fan(): pass


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

log_file = os.getenv("LOG_FILE")
if log_file:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)


# --- CONFIGURATION ---
API_URL = os.getenv("API_URL", "http://136.119.125.251:8000")
DATA_ENDPOINT = f"{API_URL}/sensors/data"
SETTINGS_ENDPOINT = f"{API_URL}/settings"

DEFAULT_INTERVAL = int(os.getenv("DEFAULT_INTERVAL", "5"))
SETTINGS_REFRESH = int(os.getenv("SETTINGS_REFRESH", "10"))

TEMP_ON_THRESHOLD = float(os.getenv("TEMP_ON_THRESHOLD", "26"))
TEMP_OFF_THRESHOLD = float(os.getenv("TEMP_OFF_THRESHOLD", "24"))


def get_settings():
    """Fetch power, interval and fan settings from backend."""
    try:
        req = urllib.request.Request(SETTINGS_ENDPOINT, method="GET")
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)

        with opener.open(req, timeout=5) as response:
            return json.loads(response.read().decode())

    except Exception as e:
        logger.error(f"Settings fetch error: {e} — using defaults")
        return {
            "power": 1,
            "interval": DEFAULT_INTERVAL,
            "fan_manual": 0
        }


def get_all_sensor_payload():
    """Collect real-time sensor data."""
    temp = read_temperature()

    return {
        "temperature": round(temp, 2) if temp is not None else 0.0,
        "humidity": 55.0,      # Placeholder
        "co2": 450,            # Placeholder
        "sound": round(read_sound(), 2),
        "light": round(read_light(), 2),
        "dust": round(read_dust(), 4),
        "motion": 0            # Placeholder
    }


def decide_fan_state(temperature: float, fan_manual: int, previous_fan_state: int) -> int:
    """
    Fan control logic:
    - If Blynk manual button is ON, fan ON.
    - If manual OFF, use automatic temperature control.
    - Uses two thresholds to avoid rapid ON/OFF switching.
    """
    if fan_manual == 1:
        return 1

    if temperature >= TEMP_ON_THRESHOLD:
        return 1

    if temperature <= TEMP_OFF_THRESHOLD:
        return 0

    return previous_fan_state


def send_to_fastapi(payload):
    """Send sensor data to the Cloud VM via POST request."""
    try:
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            DATA_ENDPOINT,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Pi-Collector"
            },
            method="POST"
        )

        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)

        with opener.open(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    except Exception as e:
        logger.error(f"Connection Error: {e}")
        return None


def main():
    logger.info("--- Raspberry Pi Sensor Collector Started ---")
    logger.info(f"Targeting Server: {DATA_ENDPOINT}")

    setup_temperature()
    setup_sound()
    setup_dust()
    setup_light()
    setup_fan()

    loop_count = 0
    interval = DEFAULT_INTERVAL
    power = 1
    fan_manual = 0
    fan_state = 0

    while True:
        try:
            if loop_count % SETTINGS_REFRESH == 0:
                settings = get_settings()
                power = settings.get("power", 1)
                interval = settings.get("interval", DEFAULT_INTERVAL)
                fan_manual = settings.get("fan_manual", 0)

                logger.info(
                    f"[Settings] Power={'ON' if power else 'OFF'} | "
                    f"Interval={interval}s | "
                    f"Fan Manual={'ON' if fan_manual else 'OFF'}"
                )

            if not power:
                logger.info(f"[{time.strftime('%H:%M:%S')}] System OFF — waiting...")
                set_fan(0)
                time.sleep(interval)
                loop_count += 1
                continue

            # 1. Read sensor data
            payload = get_all_sensor_payload()

            # 2. Fan control
            temperature = payload.get("temperature", 0.0)
            fan_state = decide_fan_state(temperature, fan_manual, fan_state)
            set_fan(fan_state)

            # Add fan state into payload for FastAPI / MySQL / Blynk
            payload["fan"] = fan_state

            # 3. Send data
            result = send_to_fastapi(payload)

            # 4. Log result
            timestamp = time.strftime('%H:%M:%S')
            sensor_data_str = " | ".join(
                [f"{k.capitalize()}: {v}" for k, v in payload.items()]
            )

            if result:
                logger.info(f"[{timestamp}] Sent Data OK >> {sensor_data_str}")
            else:
                logger.error(f"[{timestamp}] Failed to reach server at {API_URL}")

        except Exception as e:
            logger.error(f"Loop Error: {e}")

        loop_count += 1
        time.sleep(interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Collector Stopped by User.")
        cleanup_fan()