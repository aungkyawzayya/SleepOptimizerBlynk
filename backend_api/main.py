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
    logger.error("CRITICAL: GEMINI_API_KEY not found in .env!")
else:
    genai.configure(api_key=api_key)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Sleep Optimizer Online")
    asyncio.create_task(keep_blynk_alive())
    asyncio.create_task(poll_v16_trigger())   # webhook substitute: V16=1 → /analyze
    yield

async def keep_blynk_alive():
    while True:
        blynk_client.update_pin("V0", 1)
        await asyncio.sleep(30)

# --- V16 BUTTON POLLER (replaces missing Blynk HTTP-webhook on free plan) ---
# Polls V16 every 5 s. When pressed (value=1): shows "ANALYZING…" on V9,
# runs the room-check AI inline, then resets V16 to 0.
async def poll_v16_trigger():
    V16_POLL_INTERVAL = 5  # seconds
    while True:
        try:
            def _check_and_run():
                val = blynk_client.get_pin("V16")
                if val is None:
                    return
                try:
                    pressed = int(float(val)) == 1
                except ValueError:
                    return
                if not pressed:
                    return

                logger.info("[V16 POLLER] Room Check button pressed — triggering AI analysis")

                # Immediately show "ANALYZING…" so the user sees feedback
                blynk_client.update_pin("V9", "Analyzing...")
                # Reset button so it can be pressed again
                blynk_client.update_pin("V16", 0)

                # Run the AI room check
                raw_data = get_recent_sensor_data(limit=10)
                if not raw_data:
                    blynk_client.update_pin("V9", "No sensor data found.")
                    logger.warning("[V16 POLLER] No sensor data available.")
                    return

                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(
                    "You are a sleep environment advisor. "
                    f"Analyze ONLY Temperature, Sound, Light, and Dust from this data: {raw_data}. "
                    "Give ONE short sentence of advice, max 100 characters. "
                    "No markdown, no bullet points, plain text only."
                )
                report = response.text.strip()
                if len(report) > 100:
                    report = report[:97] + "..."

                blynk_client.update_pin("V9", report)
                logger.info(f"[V16 POLLER] Room Check complete: {report}")

            await asyncio.to_thread(_check_and_run)
        except Exception as e:
            logger.error(f"[V16 POLLER] Error: {e}")

        await asyncio.sleep(V16_POLL_INTERVAL)

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
            blynk_client.update_pin("V16", 0)
            return {"status": "error"}

        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            f"You are a sleep environment advisor. "
            f"Analyze ONLY Temperature, Sound, Light, and Dust from this data: {raw_data}. "
            f"Give ONE short sentence of advice, max 100 characters. "
            f"No markdown, no bullet points, plain text only."
        )
        report = response.text.strip()

        # Truncate to 100 chars just in case
        if len(report) > 100:
            report = report[:97] + "..."

        blynk_client.update_pin("V9", report)
        await asyncio.sleep(0.5)
        blynk_client.update_pin("V16", 0)

        logger.info(f"Room Check Success: {report}")
        return {"status": "success", "advice": report}

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
        raw_data = get_recent_sensor_data(limit=100)

        if not raw_data:
            blynk_client.update_pin("V10", "No data available.")
            await asyncio.sleep(0.5)
            blynk_client.update_pin("V14", 0)
            return {"status": "error"}

        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = (
            f"Sleep environment data: {raw_data}. "
            "Write a morning report in exactly 3 short lines, plain text only, no markdown: "
            "Line 1: Sleep quality score X/10. "
            "Line 2: Main issue last night. "
            "Line 3: One tip for tonight."
        )

        response = model.generate_content(prompt)
        full_report = response.text.strip()

        blynk_client.update_pin("V10", full_report)
        await asyncio.sleep(0.5)
        blynk_client.update_pin("V14", 0)

        logger.info("Morning Report Success")
        return {"status": "success", "report": full_report}

    except Exception as e:
        logger.error(f"Morning Report Error: {e}")
        blynk_client.update_pin("V10", "AI Error. Try again.")
        await asyncio.sleep(0.5)
        blynk_client.update_pin("V14", 0)
        return {"status": "error"}