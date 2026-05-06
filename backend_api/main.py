import asyncio
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
import blynk_client
from sensor_manager import SensorManager

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Sensor Manager (handles both Fake and Real states)
sensors = SensorManager(max_history=100)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("Sleep Optimizer — System Starting")
    
    # 1. Check Blynk Connectivity
    if blynk_client.check_connection():
        logger.info("[OK] Blynk Token Validated")
    else:
        logger.error("[CRITICAL] Blynk Token Invalid or Server Unreachable")

    # 2. Start Background Workers
    # This loop runs constantly. If sensors.is_fake() is True, it generates data.
    # If False, it waits for data posts from your real Raspberry Pi.
    asyncio.create_task(sensors.fake_data_loop())
    asyncio.create_task(sensors.poll_mode()) # Watches Blynk switch for Real/Fake toggle
    
    yield
    logger.info("System Shutting Down...")

app = FastAPI(title="Sleep Optimizer Dual-Mode API", lifespan=lifespan)

@app.post("/sensors/data")
async def receive_real_data(data: dict):
    """Endpoint used by your physical Raspberry Pi to post real sensor values."""
    if not sensors.is_fake():
        sensors.process(data)
        # Forward real data to Blynk immediately
        for key, val in data.items():
            if key in blynk_client.PINS:
                blynk_client.update_pin(blynk_client.PINS[key], val)
        return {"status": "Real data processed"}
    return {"status": "System in Fake Mode, ignoring real data"}

@app.get("/status")
def get_status():
    return {
        "mode": "Fake API" if sensors.is_fake() else "Raspberry Pi",
        "latest_readings": sensors.latest_data
    }