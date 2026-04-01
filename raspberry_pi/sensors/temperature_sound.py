#!/usr/bin/env python3
import os
import time
import json
import urllib.request
import urllib.error
import RPi.GPIO as GPIO

# ── Sensor / API Config ──────────────────────────────────────
ds18b20 = ""
FASTAPI_URL = "http://136.119.125.251:8000/sensors/data"

# DS18B20 uses 1-Wire on GPIO17 in your setup
# LM358 sound sensor digital output uses GPIO27
SOUND_PIN = 27


# ── Setup ────────────────────────────────────────────────────
def setup():
    global ds18b20

    # Find DS18B20 sensor ID
    for i in os.listdir('/sys/bus/w1/devices'):
        if i.startswith('28-'):
            ds18b20 = i
            print("Temperature sensor found:", ds18b20)
            break

    if not ds18b20:
        raise RuntimeError("No DS18B20 sensor found")

    # Setup sound sensor GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SOUND_PIN, GPIO.IN)

    print(f"Sound sensor ready on GPIO{SOUND_PIN}")


# ── Read Temperature ─────────────────────────────────────────
def read_temperature():
    location = f"/sys/bus/w1/devices/{ds18b20}/w1_slave"
    with open(location) as f:
        text = f.read()

    lines = text.strip().split("\n")
    if len(lines) < 2:
        raise RuntimeError("Invalid temperature sensor data format")

    secondline = lines[1]
    temperaturedata = secondline.split(" ")[9]
    return float(temperaturedata[2:]) / 1000


# ── Read Sound (LM358 digital) ───────────────────────────────
def read_sound():
    raw_value = GPIO.input(SOUND_PIN)

    # Most LM358 digital modules:
    # 0 = sound detected
    # 1 = quiet
    sound_detected = 1 if raw_value == 0 else 0

    return sound_detected, raw_value


# ── Send to FastAPI ──────────────────────────────────────────
def send_to_fastapi(temp, sound):
    payload = {
        "temperature": round(temp, 3),
        "sound": sound
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        FASTAPI_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=5) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


# ── Main Loop ────────────────────────────────────────────────
def loop():
    while True:
        try:
            temp = read_temperature()
            sound_detected, raw_sound = read_sound()

            print(f"\nCurrent temperature: {temp:.3f} C")
            print(f"Sound detected: {sound_detected} (raw={raw_sound})")

            result = send_to_fastapi(temp, sound_detected)

            status = result.get("status", "unknown")
            message = result.get("message", "")
            blynk_status = result.get("blynk_status", "unknown")
            saved_data = result.get("data", {})

            print("FastAPI status:", status)
            if message:
                print("Message:", message)
            print("Blynk status:", blynk_status)
            print("Saved data:", saved_data)

        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
            try:
                error_body = e.read().decode("utf-8")
                print("Server response:", error_body)
            except Exception:
                pass

        except urllib.error.URLError as e:
            print("Connection failed:", e)

        except Exception as e:
            print("Error:", e)

        time.sleep(5)


# ── Cleanup ──────────────────────────────────────────────────
def destroy():
    GPIO.cleanup()


if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        print("\nStopped.")
        destroy()