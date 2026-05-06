import asyncio
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from google import genai
import blynk_client
from database import get_recent_sensor_data

# 1. Load environment variables IMMEDIATELY
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. Initialize Gemini Client with explicit key check
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("CRITICAL: GOOGLE_API_KEY not found in environment!")
    client = None
else:
    client = genai.Client(api_key=api_key)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Sleep Optimizer HTTP Gateway Online")
    asyncio.create_task(keep_blynk_alive())
    yield

async def keep_blynk_alive():
    """Heartbeat to keep Blynk dashboard 'Online' status green."""
    while True:
        # Pinging V0 as heartbeat
        blynk_client.update_pin("V0", 1) 
        await asyncio.sleep(30)

app = FastAPI(title="Sleep Optimizer AI API", lifespan=lifespan)

@app.get("/settings")
def get_sensor_settings():
    return {"power": 1, "interval": 5, "fan_manual": 1}

@app.post("/analyze")
async def trigger_room_check():
    logger.info("AI Analysis Triggered via Dashboard")
    
    if client is None:
        error_msg = "AI Error: API Key Missing"
        blynk_client.update_pin("V7", error_msg)
        return {"status": "error", "message": error_msg}

    try:
        # Fetch data for analysis (retrieved from your MySQL DB)
        raw_data = get_recent_sensor_data(limit=10)
        
        if not raw_data:
            blynk_client.update_pin("V7", "No recent sensor data found.")
            return {"status": "error", "message": "No data in DB"}

        # Prepare summary for Gemini
        data_summary = str(raw_data)
        
        # Call the STABLE Gemini 1.5 Flash model
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=f"As a sleep expert, analyze this sensor data and give a 1-sentence advice for better sleep: {data_summary}"
        )
        
        report = response.text.strip()

        # Push the AI report to Blynk V7 to clear the 'ANALYZING...' hang
        blynk_client.update_pin("V7", report)
        logger.info(f"AI Report Sent: {report}")
        
        return {"status": "success", "report": report}

    except Exception as e:
        logger.error(f"Gemini API Failure: {e}")
        blynk_client.update_pin("V7", "AI Service Busy. Please try again.")
        return {"status": "error", "message": str(e)}