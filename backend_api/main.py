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
    logger.info("Sleep Optimizer API Starting")
    blynk_client.check_connection()
    # These tasks handle the internal state/fake data if no real Pi is connected
    asyncio.create_task(sensors.fake_data_loop())
    asyncio.create_task(sensors.poll_mode()) 
    yield

app = FastAPI(title="Sleep Optimizer HTTP Control", lifespan=lifespan)

@app.get("/settings")
def get_sensor_settings():
    """
    HTTP Endpoint for the Pi to fetch its configuration.
    """
    return {
        "power": "ON",
        "interval": 5, 
        "fan_manual": "OFF"
    }

@app.get("/status")
def get_status():
    return {
        "mode": "Raspberry Pi" if not sensors.is_fake() else "Fake Mode",
        "data": sensors.latest_data
    }