import os
import logging
import mysql.connector
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

logger = logging.getLogger(__name__)

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "sleep_optimizer")
    )


def truncate_sensor_data():
    """Delete all rows from sensor_data table (full reset)."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE sensor_data")
        conn.commit()
        cursor.close()
        logger.info("[DB] sensor_data table truncated.")
        return True
    except Exception as e:
        logger.error(f"[DB TRUNCATE ERROR] {e}")
        return False
    finally:
        if conn:
            conn.close()


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