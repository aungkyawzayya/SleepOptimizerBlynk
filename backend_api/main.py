import asyncio
import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
import google.generativeai as genai
import blynk_client
import gemini_sleep
from database import get_recent_sensor_data, save_sensor_data

# Cooldown timestamps — prevent runaway webhook loops
_last_analyze_time      = 0.0
_last_morning_rpt_time  = 0.0
COOLDOWN_SECONDS        = 30   # minimum gap between successive calls

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
    gemini_sleep.init_gemini()                # initialise gemini_sleep client
    logger.info("Sleep Optimizer Online")
    asyncio.create_task(keep_blynk_alive())
    asyncio.create_task(poll_v16_trigger())   # webhook substitute: V16=1 → /analyze
    asyncio.create_task(poll_v14_trigger())   # webhook substitute: V14=1 → /morning_report
    asyncio.create_task(fake_data_loop())     # auto-generate fake data when V15=1
    yield

async def keep_blynk_alive():
    # V0 is the Temperature pin — do NOT write to it here.
    # This coroutine is kept as a placeholder in case a real heartbeat pin is added.
    while True:
        await asyncio.sleep(60)

# --- FAKE DATA LOOP (V15=1 → auto-generate fake sensor data) ---
async def fake_data_loop():
    from fake_sensors import read_all
    SKIP_KEYS = {"fan"}  # V24 is user control — never overwrite it
    while True:
        try:
            def _run():
                # Check if Fake API mode is active (V15=1)
                mode_val = blynk_client.get_pin("V15")
                if mode_val is None or int(float(mode_val)) != 1:
                    return  # Pi mode — do nothing

                # Read interval from V13
                interval_val = blynk_client.get_pin("V13")
                interval = max(5, int(float(interval_val))) if interval_val else 5

                # Generate fake sensor data
                data = read_all()

                # Fan logic using same thresholds as Pi
                temp = data.get("temperature", 0)
                fan_mode_val = blynk_client.get_pin("V24")
                fan_mode = int(float(fan_mode_val)) if fan_mode_val else 0
                if fan_mode == 2:
                    data["fan"] = 0
                elif fan_mode == 1:
                    data["fan"] = 1
                else:
                    data["fan"] = 1 if temp >= 25 else 0

                # Save to DB
                save_sensor_data(data)

                # Push to Blynk (skip fan/V24)
                for key, val in data.items():
                    if key in blynk_client.PINS and key not in SKIP_KEYS:
                        blynk_client.update_pin(blynk_client.PINS[key], val)

                logger.info(f"[FAKE] Sent: Temp={data.get('temperature')}°C | "
                            f"Sound={data.get('sound')} | Light={data.get('light')} | "
                            f"Dust={data.get('dust')} | Motion={data.get('motion')} | "
                            f"Fan={data.get('fan')}")

            await asyncio.to_thread(_run)
        except Exception as e:
            logger.error(f"[FAKE ERROR] {e}")

        # Poll interval from V13 for sleep duration
        try:
            iv = blynk_client.get_pin("V13")
            sleep_secs = max(5, int(float(iv))) if iv else 5
        except Exception:
            sleep_secs = 5
        await asyncio.sleep(sleep_secs)

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

# --- V14 BUTTON POLLER (replaces missing Blynk HTTP-webhook on free plan) ---
# Polls V14 every 5 s. When pressed (value=1): shows "Generating..." on V10,
# runs the morning report AI inline, then resets V14 to 0.
async def poll_v14_trigger():
    V14_POLL_INTERVAL = 5  # seconds
    while True:
        try:
            def _check_and_run():
                val = blynk_client.get_pin("V14")
                if val is None:
                    return
                try:
                    pressed = int(float(val)) == 1
                except ValueError:
                    return
                if not pressed:
                    return

                logger.info("[V14 POLLER] Morning Report button pressed — generating report")

                # Immediately show feedback and reset button
                blynk_client.update_pin("V10", "Generating report...")
                blynk_client.update_pin("V14", 0)

                raw_data = get_recent_sensor_data(limit=100)
                if not raw_data:
                    blynk_client.update_pin("V10", "No data available.")
                    logger.warning("[V14 POLLER] No sensor data available.")
                    return

                result = gemini_sleep.morning_report(raw_data)
                if not result:
                    blynk_client.update_pin("V10", "AI Error. Try again.")
                    logger.warning("[V14 POLLER] gemini_sleep returned no result.")
                    return

                score   = result.get('score', 0)
                summary = result.get('summary', '')
                tips    = result.get('tips', '')

                blynk_client.update_pin("V10", f"Sleep Score: {score}/100")
                blynk_client.update_pin("V18", summary)
                blynk_client.update_pin("V19", tips)
                logger.info(f"[V14 POLLER] Morning Report complete: score={score}/100")

            await asyncio.to_thread(_check_and_run)
        except Exception as e:
            logger.error(f"[V14 POLLER] Error: {e}")

        await asyncio.sleep(V14_POLL_INTERVAL)


app = FastAPI(title="Sleep Optimizer AI", lifespan=lifespan)

@app.get("/settings")
def get_sensor_settings():
    # V24 fan mode: 0 = AUTO (temp-based), 1 = Force ON, 2 = Force OFF
    fan_mode = 0  # safe default: AUTO
    try:
        val = blynk_client.get_pin("V24")
        if val is not None:
            fan_mode = int(float(val))
    except Exception:
        pass

    # V13: Sensor Data Interval (seconds), min 5, max 300
    interval = 5  # safe default
    try:
        val = blynk_client.get_pin("V13")
        if val is not None:
            interval = max(5, min(300, int(float(val))))
    except Exception:
        pass

    # V12: Power toggle (1 = ON, 0 = OFF)
    power = 1  # safe default: ON
    try:
        val = blynk_client.get_pin("V12")
        if val is not None:
            power = int(float(val))
    except Exception:
        pass

    return {"power": power, "interval": interval, "fan_mode": fan_mode}

# --- ENDPOINT 1: QUICK ROOM CHECK (V16 -> V9) ---
@app.post("/analyze")
async def trigger_room_check():
    global _last_analyze_time
    now = time.time()
    if now - _last_analyze_time < COOLDOWN_SECONDS:
        logger.warning(f"[/analyze] Cooldown active — skipping ({COOLDOWN_SECONDS}s guard)")
        return {"status": "cooldown"}
    _last_analyze_time = now
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
    global _last_morning_rpt_time
    now = time.time()
    if now - _last_morning_rpt_time < COOLDOWN_SECONDS:
        logger.warning(f"[/morning_report] Cooldown active — skipping ({COOLDOWN_SECONDS}s guard)")
        return {"status": "cooldown"}
    _last_morning_rpt_time = now
    logger.info("Morning Report Generation Triggered")

    try:
        raw_data = get_recent_sensor_data(limit=100)

        if not raw_data:
            blynk_client.update_pin("V10", "No data available.")
            await asyncio.sleep(0.5)
            blynk_client.update_pin("V14", 0)
            return {"status": "error"}

        result = gemini_sleep.morning_report(raw_data)
        if not result:
            blynk_client.update_pin("V10", "AI Error. Try again.")
            await asyncio.sleep(0.5)
            blynk_client.update_pin("V14", 0)
            return {"status": "error"}

        score   = result.get('score', 0)
        summary = result.get('summary', '')
        tips    = result.get('tips', '')

        blynk_client.update_pin("V10", f"Sleep Score: {score}/100")
        blynk_client.update_pin("V18", summary)
        blynk_client.update_pin("V19", tips)
        await asyncio.sleep(0.5)
        blynk_client.update_pin("V14", 0)

        logger.info("Morning Report Success")
        return {"status": "success", "score": score, "summary": summary, "tips": tips}

    except Exception as e:
        logger.error(f"Morning Report Error: {e}")
        blynk_client.update_pin("V10", "AI Error. Try again.")
        await asyncio.sleep(0.5)
        blynk_client.update_pin("V14", 0)
        return {"status": "error"}