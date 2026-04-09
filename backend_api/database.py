import os
import logging
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "sleep_optimizer")
    )


def save_sensor_data(data: dict):
    """Persist a sensor reading to MySQL. Works for both Pi and Fake API modes."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sensor_data "
            "(temperature, humidity, co2, sound, light, dust, motion) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (data.get("temperature"), data.get("humidity"), data.get("co2"),
             data.get("sound"),       data.get("light"),   data.get("dust"),
             data.get("motion"))
        )
        conn.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"[DB ERROR] {e}")
    finally:
        if conn:
            conn.close()