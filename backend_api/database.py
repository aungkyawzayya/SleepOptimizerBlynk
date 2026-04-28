import os
import logging
import mysql.connector
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# Database Connection
# ══════════════════════════════════════════════════════════════
def get_connection():
    """Create and return a new database connection."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "sleep_optimizer")
    )


# ══════════════════════════════════════════════════════════════
# Reset / Clean Data
# ══════════════════════════════════════════════════════════════
def truncate_sensor_data():
    """Delete all rows from sensor_data table (full reset)."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM sensor_data")
        conn.commit()

        cursor.close()
        logger.info("[DB] sensor_data table cleared.")
        return True

    except Exception as e:
        logger.error(f"[DB TRUNCATE ERROR] {e}")
        return False

    finally:
        if conn:
            conn.close()


# ══════════════════════════════════════════════════════════════
# Insert Sensor Data
# ══════════════════════════════════════════════════════════════
def save_sensor_data(data: dict):
    """Persist a sensor reading to MySQL."""
    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO sensor_data 
            (temperature, humidity, co2, sound, light, dust, motion, fan)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data.get("temperature"),
                data.get("humidity"),
                data.get("co2"),
                data.get("sound"),
                data.get("light"),
                data.get("dust"),
                data.get("motion"),
                data.get("fan")   # ✅ NEW FIELD
            )
        )

        conn.commit()
        cursor.close()

    except Exception as e:
        logger.error(f"[DB INSERT ERROR] {e}")

    finally:
        if conn:
            conn.close()


# ══════════════════════════════════════════════════════════════
# Query Latest Data (optional)
# ══════════════════════════════════════════════════════════════
def get_latest_data(limit=10):
    """Fetch latest sensor records."""
    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT * FROM sensor_data
            ORDER BY id DESC
            LIMIT %s
            """,
            (limit,)
        )

        result = cursor.fetchall()
        cursor.close()
        return result

    except Exception as e:
        logger.error(f"[DB QUERY ERROR] {e}")
        return []

    finally:
        if conn:
            conn.close()


# ══════════════════════════════════════════════════════════════
# Fan Usage Statistics (optional for demo)
# ══════════════════════════════════════════════════════════════
def get_fan_usage():
    """Calculate how many times fan was ON."""
    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) FROM sensor_data WHERE fan = 1
            """
        )

        result = cursor.fetchone()
        cursor.close()

        return {"fan_on_count": result[0]}

    except Exception as e:
        logger.error(f"[DB FAN STATS ERROR] {e}")
        return {"fan_on_count": 0}

    finally:
        if conn:
            conn.close()