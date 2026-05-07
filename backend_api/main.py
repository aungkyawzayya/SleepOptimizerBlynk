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

# --- ENDPOINT 1: QUICK ROOM CHECK (V16 -> V9) ---
@app.post("/analyze")
async def trigger_room_check():
    logger.info("AI Room Check Triggered")
    
    try:
        raw_data = get_recent_sensor_data(limit=10)
        if not raw_data:
            blynk_client.update_pin("V9", "No sensor data found.")
            await asyncio.sleep(0.5)
            blynk_client.update_pin("V16", 0) # Reset button
            return {"status": "error"}

        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            f"You are a sleep environment advisor. Analyze ONLY these 4 sensors: "
            f"Temperature, Sound, Light, Dust from this data: {raw_data}. "
            f"Give ONE short sentence (max 100 characters) of advice. No markdown, no bullet points."
        )
        report = response.text.strip()

        # Update Advice and Reset Button
        blynk_client.update_pin("V9", report)
        await asyncio.sleep(0.5) # Safety delay for Blynk UI
        blynk_client.update_pin("V16", 0) 
        
        logger.info(f"Room Check Success: {report}")
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Room Check Error: {e}")
        blynk_client.update_pin("V9", "AI Error. Try again.")
        await asyncio.sleep(0.5)
        blynk_client.update_pin("V16", 0)
        return {"status": "error"}

# --- ENDPOINT 2: MORNING REPORT (V14 -> V10) ---
@app.post("/morning_report")
async def trigger_morning_report():
    logger.info("Morning Report Generation Triggered")
    
    try:
        # Fetch a larger window for the morning report (last 100 entries)
        raw_data = get_recent_sensor_data(limit=100)
        
        if not raw_data:
            blynk_client.update_pin("V10", "Error: No data.")
            await asyncio.sleep(0.5)
            blynk_client.update_pin("V14", 0) # Reset button
            return {"status": "error"}

        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = (
            f"Sleep environment data: {raw_data}. "
            "Give a morning report in exactly 3 short lines: "
            "1) Overall sleep quality score out of 10. "
            "2) Main issue last night. "
            "3) One tip for tonight. No markdown, plain text only."
        )
        
        response = model.generate_content(prompt)
        full_report = response.text.strip()

        # Update Blynk Datastream
        blynk_client.update_pin("V10", full_report)
        
        # Reset the "Generating" Button (V14)
        await asyncio.sleep(0.5) # Safety delay for Blynk UI
        blynk_client.update_pin("V14", 0)
        
        logger.info("Morning Report Success")
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Morning Report Error: {e}")
        await asyncio.sleep(0.5)
        blynk_client.update_pin("V14", 0)
        return {"status": "error"}