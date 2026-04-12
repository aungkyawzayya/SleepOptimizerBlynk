import logging
from fastapi import APIRouter, HTTPException
import blynk_client
from database import truncate_sensor_data

logger = logging.getLogger(__name__)

router = APIRouter()

# Reference to the central sensor manager
_sensors = None

def init_wiper(sensors_instance):
    """Register the main sensor manager instance so it can be cleared."""
    global _sensors
    _sensors = sensors_instance

def perform_wipe() -> bool:
    """
    Clear in-memory history and truncate the MySQL sensor_data table.
    Also wipes Blynk display pins so the dashboard reflects the reset.
    """
    # Clear in-memory deque
    if _sensors:
        _sensors.history.clear()
        _sensors.latest_data = {}

    # Truncate DB
    db_ok = truncate_sensor_data()

    # Reset Blynk text/label widgets
    for pin_key in ("ai_advice", "morning_rpt", "morning_summary", "morning_tips", "sleep_status"):
        try:
            blynk_client.update_pin(blynk_client.PINS[pin_key], " ")
        except Exception as e:
            logger.error(f"[RESET] Blynk clear failed for {pin_key}: {e}")

    # Reset numeric gauge widgets to 0
    for pin_key in ("sleep_score",):
        try:
            blynk_client.update_pin(blynk_client.PINS[pin_key], 0)
        except Exception as e:
            logger.error(f"[RESET] Blynk clear failed for {pin_key}: {e}")

    # Reset all sensor gauge pins (V0–V6)
    for pin_key in ("temperature", "humidity", "co2", "sound", "light", "dust", "motion"):
        try:
            blynk_client.update_pin(blynk_client.PINS[pin_key], 0)
        except Exception as e:
            logger.error(f"[RESET] Blynk clear failed for {pin_key}: {e}")

    logger.info(f"[RESET] Data cleared — DB truncate: {'OK' if db_ok else 'FAILED'}")
    return db_ok

@router.post("/data/reset")
def api_reset_data():
    """Reset all sensor history — clears in-memory deque, truncates MySQL, wipes Blynk widgets."""
    ok = perform_wipe()
    if not ok:
        raise HTTPException(status_code=500, detail="DB truncate failed — in-memory history still cleared")
    return {"status": "reset", "message": "All sensor data cleared successfully"}
