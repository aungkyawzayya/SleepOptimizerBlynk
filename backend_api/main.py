import asyncio
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
import google.generativeai as genai
import blynk_client
from database import get_recent_sensor_data

# 1. Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. Initialize Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("CRITICAL: GOOGLE_API_KEY not found in .env!")
else:
    genai.configure(api_key=api_key)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Sleep Optimizer Online")
    asyncio.create_task(keep_blynk_alive())
    yield

async def keep_blynk_alive():
    while True:
        blynk_client.update_pin("V0", 1) 
        await asyncio.sleep(30)

app = FastAPI(title="Sleep Optimizer AI", lifespan=lifespan)

@app.get("/settings")
def get_sensor_settings():
    return {"power": 1, "interval": 5, "fan_manual": 1}

@app.post("/analyze")
async def trigger_room_check():
    logger.info("AI Analysis Triggered")
    
    if not api_key:
        blynk_client.update_pin("V9", "Error: No API Key")
        return {"status": "error", "message": "API Key Missing"}

    try:
        # Fetch data from your MySQL database
        raw_data = get_recent_sensor_data(limit=10)
        
        if not raw_data:
            blynk_client.update_pin("V9", "Error: No Sensor Data")
            return {"status": "error", "message": "No data in DB"}

        data_summary = str(raw_data)
        
        # 3. Call Gemini using the universally supported Pro model
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"As a sleep expert, analyze this data in one short sentence: {data_summary}"
        )
        
        report = response.text.strip()

        # Update Blynk V9 (AI Advice)
        blynk_client.update_pin("V9", report)
        logger.info(f"AI Success: {report}")
        
        return {"status": "success", "report": report}

    except Exception as e:
        logger.error(f"Gemini Failure: {e}")
        blynk_client.update_pin("V9", "AI Service Error. Try again.")
        return {"status": "error", "message": str(e)}