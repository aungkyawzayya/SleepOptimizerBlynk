import asyncio
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
import blynk_client
from sensor_manager import SensorManager

# --- Robust .env Loading ---
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sensors = SensorManager(max_history=100)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("Sleep Optimizer — System Starting")
    
    # Debug: Confirm Token Visibility
    token = os.getenv("BLYNK_AUTH_TOKEN")
    if token:
        logger.info(f"[DEBUG] Auth Token detected: {token[:4]}****")
    else:
        logger.error("[DEBUG] CRITICAL: Auth Token NOT found in environment!")

    # 1. Check Blynk Connectivity
    if blynk_client.check_connection():
        logger.info("[OK] Blynk Token Validated & Dashboard Online")
    else:
        logger.error("[CRITICAL] Blynk Token Invalid or Server Unreachable")

    # 2. Start Background Workers
    asyncio.create_task(sensors.fake_data_loop())
    asyncio.create_task(sensors.poll_mode()) 
    
    yield
    logger.info("System Shutting Down...")

app = FastAPI(title="Sleep Optimizer Dual-Mode API", lifespan=lifespan)

@app.post("/sensors/data")
async def receive_real_data(data: dict):
    if not sensors.is_fake():
        sensors.process(data)
        for key, val in data.items():
            if key in blynk_client.PINS:
                blynk_client.update_pin(blynk_client.PINS[key], val)
        return {"status": "Real data processed"}
    return {"status": "System in Fake Mode"}

@app.get("/status")
def get_status():
    return {
        "mode": "Fake API" if sensors.is_fake() else "Raspberry Pi",
        "latest_readings": sensors.latest_data
    }