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

API_URL = "http://127.0.0.1:8000"
INTERVAL = 5  # seconds


def main():
    print("Fake Sensor Runner — sending data every 5s")
    print(f"Backend: {API_URL}")
    print("Press Ctrl+C to stop\n")

    count = 0
    while True:
        try:
            # Read fake sensors + push to Blynk
            r = urllib.request.urlopen(f"{API_URL}/sensors/fake", timeout=15)
            data = json.loads(r.read().decode())
            count += 1

            d = data['data']
            print(
                f"[{count}] [{data['status']}] "
                f"Temp:{d.get('temperature')}°C "
                f"Hum:{d.get('humidity')}% "
                f"CO2:{d.get('co2')}ppm "
                f"Sound:{d.get('sound')}dB "
                f"Light:{d.get('light')}lux "
                f"Dust:{d.get('dust')} "
                f"Motion:{d.get('motion')}"
            )

            # Run AI room check every 60s (every 12th call)
            if count % 12 == 0:
                print("  Running AI room check...")
                req = urllib.request.Request(f"{API_URL}/ai/room-check", method='POST')
                r = urllib.request.urlopen(req, timeout=10)
                ai = json.loads(r.read().decode())
                print(f"  Score: {ai['score']}/100 | {ai['advice']}")

        except Exception as e:
            print(f"  Error: {e}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")