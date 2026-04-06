import asyncio
import time
from datetime import datetime
from collections import deque
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Internal modules
from database import get_connection
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
sensor_history: deque = deque(maxlen=100)  # Stores the last 100 readings
start_time: float = time.time()

# ══════════════════════════════════════════════════════════════
# Lifecycle Management (Startup/Shutdown)
# ══════════════════════════════════════════════════════════════
async def _poll_morning_trigger():
    """Background task: checks V14 every 5 s and generates the morning report when the button is pressed."""
    while True:
        try:
            val = blynk_client.get_pin(blynk_client.PINS['morning_trigger'])
            if val is not None and int(float(val)) == 1:
                print("[TRIGGER] Morning Report button pressed — generating report...")
                # Reset pin immediately so a second press works
                blynk_client.update_pin(blynk_client.PINS['morning_trigger'], 0)
                if len(sensor_history) >= 5:
                    result = gemini_sleep.morning_report(list(sensor_history))
                    if result:
                        report_msg = f"Score: {result['score']} | Summary: {result['summary']}"
                        blynk_client.update_pin(blynk_client.PINS['morning_rpt'], report_msg)
                        print("[TRIGGER] Morning report sent to Blynk V10")
                else:
                    blynk_client.update_pin(blynk_client.PINS['morning_rpt'],
                                            "Not enough data yet — keep monitoring!")
        except Exception as e:
            print(f"[TRIGGER ERROR] {e}")
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print("  Sleep Optimizer — Backend Server Starting")
    print("=" * 50)

    try:
        # Check connections on startup
        if blynk_client.check_connection():
            print("[OK] Blynk: Connected")

        if gemini_sleep.init_gemini():
            print("[OK] Gemini AI: Ready")
    except Exception as e:
        print(f"[STARTUP ERROR] Initialization failed: {e}")

    trigger_task = asyncio.create_task(_poll_morning_trigger())
    yield
    trigger_task.cancel()
    print("Shutting down server...")

app = FastAPI(title="Sleep Optimizer API", version="1.5.0", lifespan=lifespan)

# ══════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════
def save_to_db(data: dict):
    """Saves sensor readings to MySQL database"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO sensor_data 
            (temperature, humidity, co2, sound, light, dust, motion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data.get("temperature"), data.get("humidity"), data.get("co2"),
            data.get("sound"), data.get("light"), data.get("dust"), data.get("motion")
        )
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"[DB ERROR] Failed to save data: {e}")
    finally:
        if conn:
            conn.close()

def process_data(data: dict):
    """Updates memory state, persists to DB, and syncs with Blynk"""
    global latest_sensor_data
    latest_sensor_data = data
    
    # Store in history with timestamp
    entry = {**data, "timestamp": datetime.now().strftime("%H:%M:%S")}
    sensor_history.append(entry)
    
    # Offload to DB and Blynk
    save_to_db(data)
    blynk_status = blynk_client.send_sensor_data(data)
    
    return {
        "status": "success",
        "blynk": "ok" if blynk_status else "failed",
        "data": data
    }

# ══════════════════════════════════════════════════════════════
# API Endpoints
# ══════════════════════════════════════════════════════════════

@app.get("/")
def home():
    return {"message": "Sleep Optimizer API is Online"}

@app.post("/sensors/data")
def receive_data(sensor_data: SensorData):
    """Endpoint for Raspberry Pi to post real-time sensor data"""
    data = sensor_data.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Empty data received")
    return process_data(data)

@app.get("/sensors/fake")
def fake_data_trigger():
    """Trigger for manual testing using simulated data"""
    from fake_sensors import read_all
    return process_data(read_all())

@app.post("/ai/room-check")
def ai_analysis(sensor_data: Optional[SensorData] = None):
    """Analyzes room environment using Gemini AI and sends advice to Blynk"""
    global latest_room_check
    
    # Use provided data or fallback to the latest stored reading
    analysis_data = latest_sensor_data
    if sensor_data:
        analysis_data = sensor_data.model_dump(exclude_none=True)

    if not analysis_data:
        raise HTTPException(status_code=400, detail="No sensor data available for AI analysis")

    # Call Gemini AI
    result = gemini_sleep.room_check(analysis_data)
    if not result:
        raise HTTPException(status_code=500, detail="AI analysis process failed")

    # Update Blynk dashboard
    try:
        blynk_client.update_pin(blynk_client.PINS['sleep_score'], result['score'])
        blynk_client.update_pin(blynk_client.PINS['ai_advice'], result['advice'])
        
        # Set Gauge color based on score
        score = result.get('score', 0)
        color = "#4CAF50" if score >= 80 else "#FF9800" if score >= 50 else "#F44336"
        blynk_client.update_property(blynk_client.PINS['sleep_score'], "color", color)
    except Exception as e:
        print(f"[BLYNK UPDATE ERROR] {e}")

    latest_room_check = result
    return result

@app.post("/ai/morning-report")
def morning_report():
    """Generates a summary report of the night's data using Gemini AI"""
    if len(sensor_history) < 5:
        raise HTTPException(status_code=400, detail="Insufficient historical data for report")
    
    result = gemini_sleep.morning_report(list(sensor_history))
    if result:
        report_msg = f"Score: {result['score']} | Summary: {result['summary']}"
        blynk_client.update_pin(blynk_client.PINS['morning_rpt'], report_msg)
    return result

@app.get("/settings")
def get_settings():
    """Returns current power and interval settings from Blynk for the Pi to poll"""
    power_raw    = blynk_client.get_pin(blynk_client.PINS['power'])
    interval_raw = blynk_client.get_pin(blynk_client.PINS['interval'])

    power    = int(float(power_raw))    if power_raw    is not None else 1
    interval = int(float(interval_raw)) if interval_raw is not None else 5
    interval = max(5, min(300, interval))  # clamp between 5s and 300s

    return {
        "power":    power,
        "interval": interval
    }

@app.get("/status")
def server_status():
    """Health check endpoint providing uptime and current state"""
    return {
        "uptime": f"{round(time.time() - start_time, 2)}s",
        "latest_read": latest_sensor_data,
        "history_count": len(sensor_history)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)