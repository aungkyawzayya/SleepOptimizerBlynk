"""
Sleep Optimizer — Dummy Data Generator
=======================================
Generates 5 nights of realistic sleep sensor data (May 4–8, 2026)
Interval: every 15 seconds | Hours: 22:00 – 07:00 (9 hrs/night)
Total rows: ~2,160 per night × 5 = ~10,800 rows

Usage:
    python3 generate_dummy_data.py
"""

import mysql.connector
import random
import math
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
    datetime(2026, 5, 4,  22, 0, 0),
    datetime(2026, 5, 5,  22, 0, 0),
    datetime(2026, 5, 6,  22, 0, 0),
    datetime(2026, 5, 7,  22, 0, 0),
    datetime(2026, 5, 8,  22, 0, 0),
]

INTERVAL_SECONDS = 15
NIGHT_DURATION   = 9 * 3600   # 9 hours in seconds

# Personality per night (so each night tells a different story)
NIGHT_PROFILES = [
    {"name": "Poor Sleep",    "base_temp": 27.5, "light_leak": 40,  "noise_level": 60,  "restless": 0.35},
    {"name": "Good Sleep",    "base_temp": 24.0, "light_leak": 2,   "noise_level": 15,  "restless": 0.08},
    {"name": "Average Sleep", "base_temp": 25.5, "light_leak": 15,  "noise_level": 30,  "restless": 0.20},
    {"name": "Hot Night",     "base_temp": 28.0, "light_leak": 5,   "noise_level": 20,  "restless": 0.25},
    {"name": "Ideal Sleep",   "base_temp": 22.5, "light_leak": 1,   "noise_level": 10,  "restless": 0.05},
]


def sleep_curve(t_ratio):
    """
    Returns a 0.0–1.0 value representing sleep depth.
    t_ratio = 0.0 (start of night) → 1.0 (end of night)
    Peak depth around 40–60% through the night.
    """
    return math.sin(math.pi * t_ratio) * 0.8 + 0.2


def generate_night(start_dt, profile):
    rows = []
    steps = NIGHT_DURATION // INTERVAL_SECONDS

    for i in range(steps):
        ts      = start_dt + timedelta(seconds=i * INTERVAL_SECONDS)
        t_ratio = i / steps   # 0.0 → 1.0 through the night
        depth   = sleep_curve(t_ratio)

        # --- Temperature ---
        # Starts warm, cools to minimum around 3–4 AM, slightly rises before waking
        temp_min   = profile["base_temp"] - 4.0
        temp_range = 4.0
        temp_cycle = temp_min + temp_range * (1 - depth) + random.uniform(-0.3, 0.3)
        temperature = round(max(18.0, min(32.0, temp_cycle)), 2)

        # --- Sound (0–255) ---
        # Quieter during deep sleep; occasional spikes (passing car, snore)
        base_sound = profile["noise_level"] * (1 - depth * 0.6)
        spike      = random.choices([0, random.uniform(80, 180)], weights=[0.97, 0.03])[0]
        sound      = round(min(255, max(0, base_sound + random.uniform(-5, 5) + spike)), 2)

        # --- Light (0–255) ---
        # Near zero at night; gradual dawn effect from ~5:30 AM
        hour_of_night = (ts.hour + ts.minute / 60)
        if hour_of_night >= 5.5 or hour_of_night < 1:   # dawn / pre-midnight
            dawn_t  = max(0, (hour_of_night - 5.5) / 1.5) if hour_of_night >= 5.5 else 0
            light   = round(profile["light_leak"] + dawn_t * 80 + random.uniform(0, 5), 2)
        else:
            light   = round(random.uniform(0, profile["light_leak"] * 0.3 + 1), 2)
        light = round(min(255, max(0, light)), 2)

        # --- Dust (mg/m³) ---
        # Stable with slight fluctuation
        dust = round(random.uniform(0.008, 0.035), 4)

        # --- Motion (0/1) ---
        # Restless early sleep and near waking; calm during deep sleep
        motion_prob = profile["restless"] * (1 - depth * 0.7)
        motion      = 1 if random.random() < motion_prob else 0

        # --- Fan (0/1) ---
        # On if temp >= 26°C
        fan = 1 if temperature >= 26.0 else 0

        rows.append((temperature, sound, light, dust, fan, motion, ts))

    return rows


def main():
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
    for night_dt, profile in zip(NIGHTS, NIGHT_PROFILES):
        print(f"  Generating: {profile['name']} — {night_dt.strftime('%Y-%m-%d')} ...")
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
