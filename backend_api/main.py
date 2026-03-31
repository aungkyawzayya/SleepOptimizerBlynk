"""
Sleep Optimizer — FastAPI Backend
==================================
Endpoints:
  GET  /                      → Health check
  GET  /status                → System status

  Sensors:
  GET  /sensors/fake          → Read fake sensors + push to Blynk
  POST /sensors/data          → Receive real sensor data from Pi
  GET  /sensors/history       → Recent sensor readings

  AI:
  POST /ai/room-check         → Score + advice for current conditions
  POST /ai/morning-report     → Overnight summary + score + tips

Run:
  cd backend_api
  python3 -m uvicorn main:app --reload --port 8000
"""

import os
import time
from datetime import datetime
from collections import deque
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

import blynk_client
import gemini_sleep


# ══════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════
class SensorData(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    co2: Optional[int] = None
    sound: Optional[float] = None
    light: Optional[float] = None
    dust: Optional[float] = None
    motion: Optional[int] = None


# ══════════════════════════════════════════════════════════════
# App State
# ══════════════════════════════════════════════════════════════
latest_sensor_data: dict = {}
latest_room_check: dict = {}
sensor_history: deque = deque(maxlen=100)
start_time: float = time.time()


# ══════════════════════════════════════════════════════════════
# Startup
# ══════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print("  Sleep Optimizer — FastAPI Backend")
    print("=" * 50)

    if blynk_client.check_connection():
        print("  Blynk: Connected!")
    else:
        print("  Blynk: Not reachable")

    if gemini_sleep.init_gemini():
        print("  Gemini AI: Ready")
    else:
        print("  Gemini AI: Disabled")

    print("=" * 50)
    yield
    print("Shutting down...")


app = FastAPI(
    title="Sleep Optimizer API",
    version="1.0.0",
    lifespan=lifespan,
)


# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════
def process_sensor_data(data: dict) -> dict:
    """Store sensor data, push to Blynk."""
    global latest_sensor_data

    latest_sensor_data = data
    entry = {**data, 'timestamp': datetime.now().strftime("%H:%M:%S")}
    sensor_history.append(entry)

    blynk_ok = blynk_client.send_sensor_data(data)

    ts = datetime.now().strftime("%H:%M:%S")
    status = "OK" if blynk_ok else "FAIL"
    print(f"[{ts}] [{status}] {data}")

    return {"status": status, "data": data}


# ══════════════════════════════════════════════════════════════
# Endpoints — General
# ══════════════════════════════════════════════════════════════
@app.get("/")
def health_check():
    return {"status": "ok", "service": "Sleep Optimizer API"}


@app.get("/status")
def get_status():
    return {
        "server": "running",
        "blynk": "connected" if blynk_client.check_connection() else "disconnected",
        "gemini": "ready" if gemini_sleep.is_available() else "disabled",
        "last_sensor_data": latest_sensor_data or None,
        "last_room_check": latest_room_check or None,
        "uptime_seconds": round(time.time() - start_time, 1),
        "history_count": len(sensor_history),
    }


# ══════════════════════════════════════════════════════════════
# Endpoints — Sensors
# ══════════════════════════════════════════════════════════════
@app.get("/sensors/fake")
def read_fake_sensors():
    """Read fake sensors, push to Blynk."""
    try:
        from fake_sensors import read_all
        data = read_all()
        return process_sensor_data(data)
    except ImportError:
        raise HTTPException(status_code=500, detail="fake_sensors module not found")


@app.post("/sensors/data")
def receive_sensor_data(sensor_data: SensorData):
    """Receive real sensor data from Raspberry Pi."""
    data = sensor_data.dict(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No sensor data provided")
    return process_sensor_data(data)


@app.get("/sensors/history")
def get_sensor_history(limit: int = 20):
    """Recent sensor readings."""
    history = list(sensor_history)
    return {"count": len(history), "data": history[-limit:]}


# ══════════════════════════════════════════════════════════════
# Endpoints — AI
# ══════════════════════════════════════════════════════════════
@app.post("/ai/room-check")
def ai_room_check(sensor_data: Optional[SensorData] = None):
    """
    AI Room Check — analyzes current conditions.
    Returns: {"score": 0-100, "advice": "short text"}
    Pushes score to Blynk V8, advice to Blynk V9.
    """
    global latest_room_check

    # Use provided data or latest stored data
    data = latest_sensor_data
    if sensor_data:
        data = sensor_data.dict(exclude_none=True)

    if not data:
        raise HTTPException(status_code=400, detail="No sensor data available. Call /sensors/fake or POST /sensors/data first.")
    if not gemini_sleep.is_available():
        raise HTTPException(status_code=503, detail="Gemini AI not configured")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] AI Room Check...")

    result = gemini_sleep.room_check(data)
    if not result:
        raise HTTPException(status_code=500, detail="AI analysis failed")

    # Push to Blynk
    blynk_client.update_pin(blynk_client.PINS['sleep_score'], result['score'])
    blynk_client.update_pin(blynk_client.PINS['ai_advice'], result['advice'])

    # Color the gauge
    score = result['score']
    if score >= 80:
        blynk_client.update_property(blynk_client.PINS['sleep_score'], 'color', '#4CAF50')
    elif score >= 50:
        blynk_client.update_property(blynk_client.PINS['sleep_score'], 'color', '#FF9800')
    else:
        blynk_client.update_property(blynk_client.PINS['sleep_score'], 'color', '#F44336')

    latest_room_check = result
    print(f"  Score: {result['score']}/100 | Advice: {result['advice']}")

    return result


@app.post("/ai/morning-report")
def ai_morning_report():
    """
    AI Morning Report — summarizes overnight data.
    Returns: {"score": 0-100, "summary": "...", "tips": "..."}
    Pushes report to Blynk V10.
    """
    if not gemini_sleep.is_available():
        raise HTTPException(status_code=503, detail="Gemini AI not configured")

    history = list(sensor_history)
    if len(history) < 3:
        raise HTTPException(status_code=400, detail="Not enough data for a report. Need at least 3 readings.")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] AI Morning Report...")

    result = gemini_sleep.morning_report(history)
    if not result:
        raise HTTPException(status_code=500, detail="AI report generation failed")

    # Push to Blynk V10
    report_text = f"Score: {result['score']}/100 | {result['summary']} | Tip: {result['tips']}"
    blynk_client.update_pin(blynk_client.PINS['morning_rpt'], report_text)

    print(f"  Score: {result['score']}/100")
    print(f"  Summary: {result['summary']}")
    print(f"  Tips: {result['tips']}")

    return result