#!/usr/bin/env python3
import time
import json
import logging
import urllib.request
import os
import grpc
import sensor_data_pb2
import sensor_data_pb2_grpc

# --- SENSOR IMPORTS (with hardware setup) ---
try:
    from sensors.temperature import read_temperature, setup_temperature
    from sensors.sound import read_sound, setup_sound
    from sensors.dust import read_dust, setup_dust
    from sensors.light import read_light, setup_light
    from sensors.fan import setup_fan, set_fan, cleanup_fan
    from sensors.motion import read_motion, setup_motion
except ImportError:
    # Dummy fallbacks for testing
    def setup_temperature(): return True
    def read_temperature(): return 25.0
    def setup_sound(): return True
    def read_sound(): return 2.0
    def setup_dust(): return True
    def read_dust(): return 0.0
    def setup_light(): return True
    def read_light(): return 150
    def setup_fan(): return True
    def set_fan(state): pass
    def cleanup_fan(): pass
    def setup_motion(): return True
    def read_motion(): return 1

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- THE FIX IS HERE ---
API_URL = "http://136.119.125.251:8080"
GRPC_HOST = "136.119.125.251:50051"
# -----------------------

def get_settings():
    try:
        req = urllib.request.Request(f"{API_URL}/settings", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return {"power": 1, "interval": 5, "fan_manual": 1}

def main():
    setup_temperature(); setup_sound(); setup_dust(); setup_light(); setup_fan(); setup_motion()
    fan_state = 0
    
    while True:
        settings = get_settings()
        if not settings.get("power", 1):
            time.sleep(settings.get("interval", 5))
            continue

        payload = {
            "temperature": round(read_temperature(), 2),
            "sound": round(read_sound(), 2),
            "light": round(read_light(), 2),
            "dust": round(read_dust(), 4),
            "motion": int(read_motion())
        }

        # Fan logic
        fan_state = 1 if (settings.get("fan_manual") == 1 or payload["temperature"] >= 26) else 0
        set_fan(fan_state)
        payload["fan"] = fan_state

        # Send via gRPC
        try:
            with grpc.insecure_channel(GRPC_HOST) as channel:
                stub = sensor_data_pb2_grpc.SensorDataServiceStub(channel)
                req = sensor_data_pb2.SensorDataRequest(**payload)
                
                # UPDATED: 15-second timeout to prevent DEADLINE_EXCEEDED errors
                stub.SendSensorData(req, timeout=15)
                
                # UPDATED: Expanded logger to show all sensor values clearly
                logger.info(
                    f"gRPC Sent OK >> "
                    f"Temp: {payload['temperature']}°C | "
                    f"Sound: {payload['sound']} | "
                    f"Light: {payload['light']} | "
                    f"Dust: {payload['dust']} | "
                    f"Motion: {payload['motion']} | "
                    f"Fan: {payload['fan']}"
                )
                
        except Exception as e:
            logger.error(f"gRPC Fail: {e}")

        time.sleep(settings.get("interval", 5))

if __name__ == "__main__":
    main()