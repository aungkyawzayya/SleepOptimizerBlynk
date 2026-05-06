import asyncio
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from google import genai
import blynk_client
from database import get_recent_sensor_data

# 1. Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. Initialize Gemini Client with explicit API Version v1
# This prevents the 404 error you saw earlier
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("CRITICAL: GOOGLE_API_KEY not found in .env!")
    client = None
else:
    client = genai.Client(
        api_key=api_key,
        http_options={'api_version': 'v1'}
    )

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
    
    if client is None:
        blynk_client.update_pin("V7", "Error: No API Key")
        return {"status": "error", "message": "API Key Missing"}

    try:
        # Fetch data from your MySQL database
        raw_data = get_recent_sensor_data(limit=10)
        
        if not raw_data:
            blynk_client.update_pin("V7", "Error: No Sensor Data")
            return {"status": "error", "message": "No data in DB"}

        data_summary = str(raw_data)
        
        # 3. Call Gemini using the FULL model path
        # Using 'models/gemini-1.5-flash' ensures it is found
        response = client.models.generate_content(
            model='models/gemini-1.5-flash', 
            contents=f"As a sleep expert, analyze this data in one short sentence: {data_summary}"
        )
        
        report = response.text.strip()

        # Update Blynk V7 to clear the 'ANALYZING...' text
        blynk_client.update_pin("V7", report)
        logger.info(f"AI Success: {report}")
        
        return {"status": "success", "report": report}

    except Exception as e:
        logger.error(f"Gemini Failure: {e}")
        blynk_client.update_pin("V7", "AI Service Error. Try again.")
        return {"status": "error", "message": str(e)}