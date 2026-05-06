import asyncio
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from google import genai  # New library
import blynk_client
from database import get_recent_sensor_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the new Gemini Client
# It will automatically find 'GOOGLE_API_KEY' in your .env
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Sleep Optimizer Online")
    asyncio.create_task(keep_blynk_alive())
    yield

async def keep_blynk_alive():
    while True:
        # Pinging V0 for 'Online' status
        blynk_client.update_pin("V0", 1) 
        await asyncio.sleep(30)

app = FastAPI(lifespan=lifespan)

@app.post("/analyze")
async def trigger_room_check():
    logger.info("AI Analysis Triggered")
    try:
        # 1. Fetch the data you saw in MySQL Workbench (image_79ab52.jpg)
        raw_data = get_recent_sensor_data(limit=10)
        if not raw_data:
            return {"status": "error", "message": "No data available"}

        # 2. Format the data for Gemini
        data_summary = str(raw_data)
        
        # 3. Call Gemini using the NEW SDK
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=f"As a sleep expert, analyze this sensor data and give a 1-sentence advice: {data_summary}"
        )
        
        report = response.text

        # 4. Update Blynk (V7) to clear the "ANALYZING..." text
        blynk_client.update_pin("V7", report)
        
        return {"status": "success", "report": report}

    except Exception as e:
        logger.error(f"AI Failure: {e}")
        # If Gemini fails, at least clear the "Analyzing" state with an error message
        blynk_client.update_pin("V7", "AI Service Error. Check API Key.")
        return {"status": "error", "message": str(e)}