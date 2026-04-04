"""
Fake Sensor Runner
===================
Calls the backend API every 5 seconds to simulate continuous sensor data.
Run this while the FastAPI backend is running.

Usage:
  python3 run_fake.py
"""

import urllib.request
import time
import json
import socket

# Ensure no trailing slash
API_URL = "http://136.119.125.251".rstrip('/')  # Port 80
INTERVAL = 5  # seconds


def main():
    print("Fake Sensor Runner — sending data every 5s")
    print(f"Backend: {API_URL}")
    
    # Quick connectivity check
    try:
        urllib.request.urlopen(API_URL, timeout=5)
        print("Backend is reachable. Starting loop...\n")
    except Exception as e:
        print(f"Warning: Could not reach backend at {API_URL}. It might be down. Error: {e}\n")

    print("Press Ctrl+C to stop\n")

    count = 0
    while True:
        try:
            # Read fake sensors + push to Blynk
            req = urllib.request.Request(f"{API_URL}/sensors/fake", method="GET")
            r = urllib.request.urlopen(req, timeout=15)
            data = json.loads(r.read().decode())
            count += 1

            # Extract data safely 
            d = data.get('data', {})
            status = data.get('status', 'OK')
            
            print(
                f"[{count}] [{status}] "
                f"Temp:{d.get('temperature', 'N/A')}°C "
                f"Hum:{d.get('humidity', 'N/A')}% "
                f"CO2:{d.get('co2', 'N/A')}ppm "
                f"Sound:{d.get('sound', 'N/A')}dB "
                f"Light:{d.get('light', 'N/A')}lux "
                f"Dust:{d.get('dust', 'N/A')} "
                f"Motion:{d.get('motion', 'N/A')}"
            )

            # Run AI room check every 60s (every 12th call)
            if count % 12 == 0:
                print("  Running AI room check...")
                req = urllib.request.Request(f"{API_URL}/ai/room-check", method='POST')
                r = urllib.request.urlopen(req, timeout=10)
                ai = json.loads(r.read().decode())
                print(f"  Score: {ai.get('score', 'N/A')}/100 | {ai.get('advice', 'No advice')}")

        except Exception as e:
            print(f"  Error: {e}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")