import asyncio
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
import blynk_client
from sensor_manager import SensorManager

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sensors = SensorManager(max_history=100)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Sleep Optimizer HTTP API Starting")
    blynk_client.check_connection()
    # Pings Blynk every 30s so the dashboard status stays 'Online'
    asyncio.create_task(keep_blynk_alive())
    yield

async def keep_blynk_alive():
    while True:
        # Update a heartbeat pin (V0) to show the system is active
        blynk_client.update_pin("V0", 1) 
        await asyncio.sleep(30)

app = FastAPI(title="Sleep Optimizer Control", lifespan=lifespan)

@app.get("/settings")
def get_sensor_settings():
    return {
        "power": 1,
        "interval": 5,
        "fan_manual": 1
    }