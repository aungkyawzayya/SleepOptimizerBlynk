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
import data_wiper

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

log_file = os.getenv("LOG_FILE")
if log_file:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)

# ══════════════════════════════════════════════════════════════
# Data Model
# ══════════════════════════════════════════════════════════════
class SensorData(BaseModel):
    temperature: Optional[float] = None
    sound:       Optional[float] = None
    light:       Optional[float] = None
    dust:        Optional[float] = None
    fan:         Optional[int]   = None

# ══════════════════════════════════════════════════════════════
# App State & Initializations
# ══════════════════════════════════════════════════════════════
sensors       = SensorManager(max_history=100)
ai_advice     = AIAdvice()
morning_rpt   = MorningReport()
start_time    = time.time()

runtime_settings = {
    "fan_manual": 0
}

data_wiper.init_wiper(sensors)

# ══════════════════════════════════════════════════════════════
# Lifecycle Management
# ══════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("Sleep Optimizer — Backend Starting")
    logger.info("=" * 50)

    try:
        if blynk_client.check_connection():
            logger.info("[OK] Blynk Connected")
            
            # Reset Fan Manual button to AUTO/OFF on startup
            try:
                blynk_client.update_pin(blynk_client.PINS["fan_manual"], 0)
                runtime_settings["fan_manual"] = 0
                logger.info("[INIT] Fan manual reset to AUTO/OFF")
            except Exception as e:
                logger.error(f"[INIT FAN RESET ERROR] {e}")

        if gemini_sleep.init_gemini():
            logger.info("[OK] Gemini Ready")

    except Exception as e:
        logger.error(f"[STARTUP ERROR] {e}")

    # Start all background workers
    tasks = [
        asyncio.create_task(morning_rpt.poll_trigger(lambda: list(sensors.history))),
        asyncio.create_task(ai_advice.poll_trigger(lambda: sensors.latest_data)),
        asyncio.create_task(sensors.poll_mode()),
        asyncio.create_task(sensors.fake_data_loop()),
        asyncio.create_task(sensors.poll_reset_trigger()),
    ]

    yield

    # Clean shutdown
    for t in tasks:
        t.cancel()
    logger.info("Shutting down server...")

app = FastAPI(title="Sleep Optimizer API", version="3.2.0", lifespan=lifespan)
app.include_router(data_wiper.router)

# ══════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════
@app.get("/")
def home():
    return {"message": "Sleep Optimizer API is Online"}

@app.post("/sensors/data")
def receive_data(sensor_data: SensorData):
    """Receive data from Raspberry Pi or Simulation."""
    if not sensors.power_on:
        raise HTTPException(status_code=503, detail="Power OFF")

    data = sensor_data.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Empty data")

    return sensors.process(data, save_fn=save_sensor_data)

@app.get("/settings")
def get_settings():
    """Pi/Simulation polls settings here."""
    interval_raw = blynk_client.get_pin(blynk_client.PINS["interval"])
    interval = int(float(interval_raw)) if interval_raw else 5
    interval = max(5, min(300, interval))

    fan_manual = runtime_settings["fan_manual"]
    try:
        fan_raw = blynk_client.get_pin(blynk_client.PINS["fan_manual"])
        if fan_raw is not None:
            fan_manual = int(float(fan_raw))
    except Exception as e:
        logger.error(f"[BLYNK FAN MANUAL ERROR] {e}")

    runtime_settings["fan_manual"] = fan_manual
    return {
        "power": 1 if sensors.power_on else 0,
        "interval": interval,
        "fan_manual": fan_manual
    }

@app.post("/settings/fan/{fan_manual}")
def set_fan_manual(fan_manual: int):
    """Sets manual fan control from API/UI."""
    if fan_manual not in [0, 1]:
        raise HTTPException(status_code=400, detail="Invalid value")

    runtime_settings["fan_manual"] = fan_manual
    try:
        blynk_client.update_pin(blynk_client.PINS["fan_manual"], fan_manual)
    except Exception as e:
        logger.error(f"[BLYNK FAN MANUAL UPDATE ERROR] {e}")

    return {"status": "ok", "fan_manual": fan_manual}

@app.get("/status")
def server_status():
    """Health check endpoint."""
    return {
        "uptime": f"{round(time.time() - start_time, 2)}s",
        "mode": "Fake API" if sensors.is_fake() else "Raspberry Pi",
        "latest": sensors.latest_data,
        "fan_manual": runtime_settings["fan_manual"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)