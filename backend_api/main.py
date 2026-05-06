import asyncio
import time
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
load_dotenv() # Crucial: Loads your BLYNK_AUTH_TOKEN from .env

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Internal modules
from database import save_sensor_data
import blynk_client
import gemini_sleep
from sensor_manager import SensorManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SensorData(BaseModel):
    temperature: Optional[float] = None
    sound:       Optional[float] = None
    light:       Optional[float] = None
    motion:      Optional[int]   = None

sensors = SensorManager(max_history=100)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("Sleep Optimizer Backend — Starting Up")
    logger.info("=" * 50)

    # Verify Blynk Connection
    if blynk_client.check_connection():
        logger.info("[OK] Blynk Connected")
    else:
        logger.error("[FAIL] Blynk Connection Failed - Check your Auth Token")

    # Verify Gemini initialization
    if gemini_sleep.init_gemini():
        logger.info("[OK] Gemini Ready")

    # Start Simulation Loop
    asyncio.create_task(sensors.fake_data_loop())
    
    yield
    logger.info("Shutting down server...")

app = FastAPI(title="Sleep Optimizer API", lifespan=lifespan)

@app.get("/status")
def server_status():
    return {
        "mode": "Fake API" if sensors.is_fake() else "Raspberry Pi",
        "blynk_status": "Connected" if blynk_client.check_connection() else "Disconnected",
        "latest": sensors.latest_data
    }