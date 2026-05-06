import os
import logging
import mysql.connector
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

logger = logging.getLogger(__name__)


def get_connection():
    """Create and return a new database connection."""
    # Updated default to 'lisa' to match VM configuration
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "lisa"), 
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "sleep_optimizer")
    )


def truncate_sensor_data():
    """Delete all rows from sensor_data table."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE sensor_data") # Changed to TRUNCATE to reset IDs
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


def save_sensor_data(data: dict):
    """Persist a sensor reading to MySQL."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO sensor_data
            (temperature, sound, light, dust, motion, fan)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                data.get("temperature"),
                data.get("sound"),
                data.get("light"),
                data.get("dust"),
                data.get("motion"),
                data.get("fan")
            )
        )

        conn.commit()
        cursor.close()

        logger.info(f"[DB INSERT OK] motion={data.get('motion')} fan={data.get('fan')}")

    except Exception as e:
        logger.error(f"[DB INSERT ERROR] {e}")

    finally:
        if conn:
            conn.close()


def get_recent_sensor_data(limit=20):
    """
    Fetches the most recent sensor readings for AI analysis.
    This fixes the ImportError in main.py.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        # Use created_at if available, otherwise order by ID
        query = "SELECT * FROM sensor_data ORDER BY id DESC LIMIT %s"
        cursor.execute(query, (limit,))
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        logger.error(f"[DB RETRIEVAL ERROR] {e}")
        return []
    finally:
        if conn:
            conn.close()


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


def get_fan_usage():
    """Calculate how many records show fan ON."""
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


def get_motion_usage():
    """Calculate how many records detect motion."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) FROM sensor_data WHERE motion = 1
            """
        )

        result = cursor.fetchone()
        cursor.close()

        return {"motion_detected_count": result[0]}

    except Exception as e:
        logger.error(f"[DB MOTION STATS ERROR] {e}")
        return {"motion_detected_count": 0}

    finally:
        if conn:
            conn.close()