#!/usr/bin/env python3
import time
import json
import urllib.request
import urllib.error
import os

# --- SENSOR IMPORTS ---
try:
    from sensors.temperature import read_temperature, setup_temperature
    from sensors.sound import read_sound, setup_sound
except ImportError:
    print("Warning: Sensor modules not found. Using dummy values.")
    def read_temperature(): return 25.0
    def setup_temperature(): return True
    def read_sound(): return 0.0
    def setup_sound(): return True

# --- CONFIGURATION ---
API_URL = "http://136.119.125.251"  # Port 80 — avoids iPhone hotspot port blocking
DATA_ENDPOINT     = f"{API_URL}/sensors/data"
SETTINGS_ENDPOINT = f"{API_URL}/settings"
DEFAULT_INTERVAL  = 5   # seconds fallback if Blynk unreachable
SETTINGS_REFRESH  = 10  # how many loops before re-fetching settings

def get_settings():
    """Fetch power and interval settings from the backend (which reads from Blynk)"""
    try:
        req = urllib.request.Request(SETTINGS_ENDPOINT, method="GET")
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        with opener.open(req, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Settings fetch error: {e} — using defaults")
        return {"power": 1, "interval": DEFAULT_INTERVAL}

def get_all_sensor_payload():
    """Collects data from all connected sensors"""
    temp = read_temperature()
    
    # Update these values as you connect your physical hardware
    return {
        "temperature": round(temp, 2) if temp is not None else 0.0,
        "humidity": 55.0,  # Replace with actual read_humidity()
        "co2": 450,        # Replace with actual read_co2()
        "sound": read_sound(),
        "light": 180,      # Replace with actual read_light()
        "dust": 0.02,      # Replace with actual read_dust()
        "motion": 0        # Replace with actual read_motion()
    }

def send_to_fastapi(payload):
    """Sends sensor data to the Cloud VM via POST request"""
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
        # Explicitly bypass any system/university proxy settings
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        with opener.open(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

def main():
    print("--- Raspberry Pi Sensor Collector Started ---")
    print(f"Targeting Server: {DATA_ENDPOINT}")
    setup_temperature()
    setup_sound()

    loop_count = 0
    interval   = DEFAULT_INTERVAL
    power      = 1  # assume on by default

    while True:
        try:
            # Refresh settings from Blynk every SETTINGS_REFRESH loops
            if loop_count % SETTINGS_REFRESH == 0:
                settings = get_settings()
                power    = settings.get("power", 1)
                interval = settings.get("interval", DEFAULT_INTERVAL)
                print(f"[Settings] Power={'ON' if power else 'OFF'} | Interval={interval}s")

            if not power:
                print(f"[{time.strftime('%H:%M:%S')}] System OFF — waiting...")
                time.sleep(interval)
                loop_count += 1
                continue

            payload = get_all_sensor_payload()
            result  = send_to_fastapi(payload)

            if result:
                timestamp = time.strftime('%H:%M:%S')
                status = result.get('status', 'unknown')
                print(f"[{timestamp}] Sent: {payload['temperature']}°C | Server Status: {status}")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Failed to reach server at {API_URL}")

        except Exception as e:
            print(f"Loop Error: {e}")

        loop_count += 1
        time.sleep(interval)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCollector Stopped.")