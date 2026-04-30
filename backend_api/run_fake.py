"""
Fake Sensor Runner (Sprint 5 Updated)
=====================================
Synchronized with 4-sensor suite: Temp, Sound(0-100), Light(0-255), Dust(mg/m3).
"""

import urllib.request
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://136.119.125.251").rstrip('/')
INTERVAL = int(os.getenv("FAKE_INTERVAL", "5"))

def main():
    print(f"Fake Sensor Runner — Backend: {API_URL}")
    
    count = 0
    while True:
        try:
            # 1. Trigger the fake sensor generation and push to Blynk
            req = urllib.request.Request(f"{API_URL}/sensors/fake", method="GET")
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            
            count += 1
            d = data.get('data', {})
            
            # 2. Updated Print Statement to match your 4-sensor project
            print(
                f"[{count}] Status: {data.get('status', 'OK')} | "
                f"Temp: {d.get('temperature', 'N/A')}°C | "
                f"Sound: {d.get('sound', 'N/A')}/100 | "
                f"Light: {d.get('light', 'N/A')}/255 | "
                f"Dust: {d.get('dust', 'N/A')} mg/m3"
            )

            # 3. AI Room Check - Update endpoint to match your AIAdvice logic
            # Every 12 calls (~60 seconds)
            if count % 12 == 0:
                print("  --> Triggering Gemini AI Room Analysis...")
                # Note: This simulates pressing the V16 button via API
                req_ai = urllib.request.Request(
                    f"{API_URL}/ai/room-check", # Ensure this route exists in your FastAPI
                    data=json.dumps({}).encode('utf-8'),
                    headers={"Content-Type": "application/json"},
                    method='POST'
                )
                with urllib.request.urlopen(req_ai, timeout=15) as r_ai:
                    ai_res = json.loads(r_ai.read().decode())
                    print(f"  [AI] Score: {ai_res.get('score', 'N/A')} | Advice: {ai_res.get('advice', '...')[:50]}...")

        except Exception as e:
            print(f"  Loop Error: {e}")

        time.sleep(INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSimulation stopped.")