"""
Sleep Optimizer — Dummy Data Generator
=======================================
Generates realistic sleep sensor data (May 4–8, 2026)
Interval: every 15 seconds | Hours: 22:00 – 07:00 (9 hrs/night)

Usage:
    python3 generate_dummy_data.py        → insert ALL 5 nights
    python3 generate_dummy_data.py 1      → insert Monday only (May 4)
    python3 generate_dummy_data.py 2      → insert Tuesday only (May 5)
    python3 generate_dummy_data.py 3      → insert Wednesday only (May 6)
    python3 generate_dummy_data.py 4      → insert Thursday only (May 7)
    python3 generate_dummy_data.py 5      → insert Friday only (May 8)
"""

import mysql.connector
import random
import math
import sys
from datetime import datetime, timedelta

# --- DB Config ---
DB_CONFIG = {
    "host":     "127.0.0.1",
    "user":     "root",
    "password": "root1234",
    "database": "sleep_optimizer"
}

# --- 5 nights: start dates ---
NIGHTS = [
    datetime(2026, 5, 4,  22, 0, 0),  # 1 - Monday
    datetime(2026, 5, 5,  22, 0, 0),  # 2 - Tuesday
    datetime(2026, 5, 6,  22, 0, 0),  # 3 - Wednesday
    datetime(2026, 5, 7,  22, 0, 0),  # 4 - Thursday
    datetime(2026, 5, 8,  22, 0, 0),  # 5 - Friday
]

NIGHT_PROFILES = [
    {"name": "Poor Sleep",    "base_temp": 27.5, "light_leak": 40,  "noise_level": 60,  "restless": 0.35},
    {"name": "Good Sleep",    "base_temp": 24.0, "light_leak": 2,   "noise_level": 15,  "restless": 0.08},
    {"name": "Average Sleep", "base_temp": 25.5, "light_leak": 15,  "noise_level": 30,  "restless": 0.20},
    {"name": "Hot Night",     "base_temp": 28.0, "light_leak": 5,   "noise_level": 20,  "restless": 0.25},
    {"name": "Ideal Sleep",   "base_temp": 22.5, "light_leak": 1,   "noise_level": 10,  "restless": 0.05},
]

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def sleep_curve(t_ratio):
    return math.sin(math.pi * t_ratio) * 0.8 + 0.2


def generate_night(start_dt, profile):
    rows = []
    steps = (9 * 3600) // 15
    for i in range(steps):
        ts      = start_dt + timedelta(seconds=i * 15)
        t_ratio = i / steps
        depth   = sleep_curve(t_ratio)

        temp_min   = profile["base_temp"] - 4.0
        temperature = round(max(18.0, min(32.0, temp_min + 4.0 * (1 - depth) + random.uniform(-0.3, 0.3))), 2)

        base_sound = profile["noise_level"] * (1 - depth * 0.6)
        spike      = random.choices([0, random.uniform(80, 180)], weights=[0.97, 0.03])[0]
        sound      = round(min(255, max(0, base_sound + random.uniform(-5, 5) + spike)), 2)

        hour_f = ts.hour + ts.minute / 60
        if hour_f >= 5.5:
            dawn_t = (hour_f - 5.5) / 1.5
            light  = round(min(255, profile["light_leak"] + dawn_t * 80 + random.uniform(0, 5)), 2)
        else:
            light  = round(random.uniform(0, profile["light_leak"] * 0.3 + 1), 2)

        dust   = round(random.uniform(0.008, 0.035), 4)
        motion = 1 if random.random() < profile["restless"] * (1 - depth * 0.7) else 0
        fan    = 1 if temperature >= 26.0 else 0

        rows.append((temperature, sound, light, dust, fan, motion, ts))
    return rows


def main():
    # Determine which nights to insert
    if len(sys.argv) > 1:
        try:
            day_num = int(sys.argv[1])
            if day_num < 1 or day_num > 5:
                print("Day number must be 1–5")
                sys.exit(1)
            selected = [(NIGHTS[day_num - 1], NIGHT_PROFILES[day_num - 1], DAY_NAMES[day_num - 1])]
        except ValueError:
            print("Usage: python3 generate_dummy_data.py [1-5]")
            sys.exit(1)
    else:
        selected = list(zip(NIGHTS, NIGHT_PROFILES, DAY_NAMES))

    print("Connecting to database...")
    conn   = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
        INSERT INTO sensor_data
            (temperature, sound, light, dust, fan, motion, created_at)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s)
    """

    total = 0
    for night_dt, profile, day_name in selected:
        print(f"  Generating: {day_name} — {profile['name']} ({night_dt.strftime('%Y-%m-%d')}) ...")
        rows = generate_night(night_dt, profile)
        cursor.executemany(sql, rows)
        conn.commit()
        total += len(rows)
        print(f"    ✓ {len(rows)} rows inserted")

    cursor.close()
    conn.close()
    print(f"\nDone! Total rows inserted: {total}")


if __name__ == "__main__":
    main()
