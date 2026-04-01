#!/usr/bin/env python3
import os
import time
import json
import urllib.request

ds18b20 = ""
FASTAPI_URL = "http://136.119.125.251:8000/sensors/data"

def setup():
    global ds18b20
    for i in os.listdir('/sys/bus/w1/devices'):
        if i.startswith('28-'):
            ds18b20 = i
            print("Sensor found:", ds18b20)
            break

    if not ds18b20:
        raise RuntimeError("No DS18B20 sensor found")

def read_temperature():
    location = f"/sys/bus/w1/devices/{ds18b20}/w1_slave"
    with open(location) as f:
        text = f.read()

    secondline = text.split("\n")[1]
    temperaturedata = secondline.split(" ")[9]
    return float(temperaturedata[2:]) / 1000

def send_to_fastapi(temp):
    payload = {
        "temperature": temp
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        FASTAPI_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=5) as response:
        return response.read().decode("utf-8")

def loop():
    while True:
        temp = read_temperature()
        print(f"Current temperature: {temp:.3f} C")

        try:
            result = send_to_fastapi(temp)
            print("FastAPI response:", result)
        except Exception as e:
            print("Send failed:", e)

        time.sleep(5)

if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        print("Stopped.")