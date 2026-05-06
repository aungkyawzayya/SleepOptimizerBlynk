import asyncio
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
import blynk_client
from database import get_recent_sensor_data # Ensure this function exists

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Sleep Optimizer HTTP Gateway Online")
    # Start the heartbeat task to fix the "Offline" status
    asyncio.create_task(keep_blynk_alive())
    yield

async def keep_blynk_alive():
    while True:
        # Pinging V0 to keep the dashboard "Online"
        blynk_client.update_pin("V0", 1) 
        await asyncio.sleep(30)

app = FastAPI(title="Sleep Optimizer Control", lifespan=lifespan)

@app.get("/settings")
def get_sensor_settings():
    # Settings fetched by your Raspberry Pi
    return {
        "power": 1,
        "interval": 5,
        "fan_manual": 1
    }

@app.post("/analyze")
async def trigger_room_check():
    """
    Triggered when you click 'CHECK NOW' on the dashboard.
    It fetches the 26+ rows you have in DB and generates a report.
    """
    logger.info("AI Analysis Triggered")
    try:
        # 1. Fetch data from DB (The rows you saw in image_79ab52.jpg)
        data = get_recent_sensor_data(limit=20) 
        
        if not data:
            return {"status": "error", "message": "No data found"}

        # 2. Logic for Analysis (Example)
        avg_temp = sum(d['temperature'] for d in data) / len(data)
        
        report = f"Analysis Complete. Avg Temp: {avg_temp:.2f}C. "
        if avg_temp > 25:
            report += "Conditions are slightly warm for sleep."
        else:
            report += "Temperature is optimal."

        # 3. Update Blynk Label (V7) to remove "ANALYZING..."
        blynk_client.update_pin("V7", report)
        
        return {"status": "success", "report": report}
    except Exception as e:
        logger.error(f"AI Analysis Failed: {e}")
        return {"status": "error", "message": str(e)}