import asyncio
import time
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Internal modules
from database import save_sensor_data
import blynk_client
import gemini_sleep
from ai_advice import AIAdvice
from morning_report import MorningReport
from sensor_manager import SensorManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add file logging if LOG_FILE is set
log_file = os.getenv("LOG_FILE")
if log_file:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)

# ══════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════
class SensorData(BaseModel):
    temperature: Optional[float] = None
    humidity:    Optional[float] = None
    co2:         Optional[int]   = None
    sound:       Optional[float] = None
    light:       Optional[float] = None
    dust:        Optional[float] = None
    motion:      Optional[int]   = None

# ══════════════════════════════════════════════════════════════
# App State
# ══════════════════════════════════════════════════════════════
sensors       = SensorManager(max_history=100)
ai_advice     = AIAdvice()
morning_rpt   = MorningReport()
latest_check: dict = {}
start_time    = time.time()

# save_sensor_data is imported from database.py and shared across Pi + Fake modes

# ══════════════════════════════════════════════════════════════
# Lifecycle
# ══════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("  Sleep Optimizer — Backend Server Starting")
    logger.info("=" * 50)

    try:
        if blynk_client.check_connection():
            logger.info("[OK] Blynk: Connected")
            # Clear stale values from previous session
            blynk_client.update_pin(blynk_client.PINS['morning_rpt'], " ")
            blynk_client.update_pin(blynk_client.PINS['ai_advice'], " ")
            blynk_client.update_pin(blynk_client.PINS['sleep_score'], " ")  # Optionally clearing score too
            blynk_client.update_property(blynk_client.PINS['power'], "label", "Power")
            blynk_client.update_property(blynk_client.PINS['room_check_trigger'], "label", "Room Check AI")
        if gemini_sleep.init_gemini():
            logger.info("[OK] Gemini AI: Ready")
    except Exception as e:
        logger.error(f"[STARTUP ERROR] {e}")

    tasks = [
        asyncio.create_task(morning_rpt.poll_trigger(lambda: list(sensors.history))),
        asyncio.create_task(ai_advice.poll_trigger(lambda: sensors.latest_data)),
        asyncio.create_task(sensors.poll_mode()),
        asyncio.create_task(sensors.fake_data_loop()),
    ]
    yield
    for t in tasks:
        t.cancel()
    logger.info("Shutting down server...")

app = FastAPI(title="Sleep Optimizer API", version="2.0.0", lifespan=lifespan)

# ══════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════
@app.get("/")
def home():
    return {"message": "Sleep Optimizer API is Online"}


@app.post("/sensors/data")
def receive_data(sensor_data: SensorData):
    """Raspberry Pi posts real-time sensor data here."""
    if not sensors.power_on:
        raise HTTPException(status_code=503, detail="Power is OFF — data rejected")
    data = sensor_data.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Empty data received")
    return sensors.process(data, save_fn=save_sensor_data)


@app.get("/sensors/fake")
def fake_data_trigger():
    """Manual fake-data trigger — useful for quick tests from MacBook."""
    from fake_sensors import read_all
    return sensors.process(read_all(), save_fn=save_sensor_data)


@app.post("/ai/room-check")
def ai_analysis(sensor_data: Optional[SensorData] = None):
    """Analyse current room environment with Gemini AI."""
    global latest_check

    data = sensors.latest_data
    if sensor_data:
        data = sensor_data.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No sensor data available")

    result = ai_advice.run(data)
    if not result:
        raise HTTPException(status_code=500, detail="AI analysis failed")

    latest_check = result
    return result


@app.post("/ai/morning-report")
def morning_report_endpoint():
    """Generate a Gemini morning sleep report from overnight history."""
    result = morning_rpt.generate(list(sensors.history))
    if not result:
        raise HTTPException(status_code=400, detail="Insufficient data or generation failed")
    return result


@app.get("/settings")
def get_settings():
    """
    Raspberry Pi polls this for power and interval settings.
    Power reflects the Blynk button state regardless of mode.
    """
    interval_raw = blynk_client.get_pin(blynk_client.PINS['interval'])
    interval = int(float(interval_raw)) if interval_raw is not None else 5
    interval = max(5, min(300, interval))  # clamp 5 – 300 s
    return {"power": 1 if sensors.power_on else 0, "interval": interval}


@app.get("/status")
def server_status():
    """Health-check endpoint with uptime and current state."""
    return {
        "uptime":        f"{round(time.time() - start_time, 2)}s",
        "mode":          "Fake API" if sensors.is_fake() else "Raspberry Pi",
        "latest_read":   sensors.latest_data,
        "history_count": len(sensors.history),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
