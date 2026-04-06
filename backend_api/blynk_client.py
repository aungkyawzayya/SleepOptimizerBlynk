"""
Sleep Optimizer — Blynk HTTPS API Client
========================================
Handles communication with Blynk Cloud via HTTPS API.
Safer version for debugging and partial sensor payloads.
"""

import os
import json
import urllib.request
import urllib.parse

BLYNK_AUTH = os.getenv("BLYNK_AUTH_TOKEN", "").strip()
BLYNK_SERVER = os.getenv("BLYNK_SERVER", "ny3.blynk.cloud").strip()
BLYNK_BASE_URL = f"https://{BLYNK_SERVER}/external/api"

# Only keep pins you really use now
PINS = {
    "temperature": 0,   # V0
    "humidity":    1,   # V1
    "co2":         2,   # V2
    "sound":       3,   # V3
    "light":       4,   # V4
    "dust":        5,   # V5
    "motion":      6,   # V6
    "sleep_score": 8,   # V8
    "ai_advice":   9,   # V9
    "morning_rpt": 10,  # V10
    "interval":         13,  # V13 — reading interval (seconds)
    "power":            12,  # V12 — system power on/off
    "morning_trigger":  14,  # V14 — button to generate morning report on demand
    "data_source":      15,  # V15 — 0 = Raspberry Pi | 1 = Fake API
}


def _has_auth() -> bool:
    return bool(BLYNK_AUTH)


def update_pin(pin: int, value) -> bool:
    """Update one Blynk virtual pin."""
    if not _has_auth():
        print("[BLYNK] Missing BLYNK_AUTH_TOKEN")
        return False

    if value is None:
        print(f"[BLYNK] Skip V{pin}: value is None")
        return True

    url = f"{BLYNK_BASE_URL}/update?token={BLYNK_AUTH}&V{pin}={urllib.parse.quote(str(value))}"
    print(f"[BLYNK] Sending V{pin} = {value}")

    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            print(f"[BLYNK] V{pin} OK (HTTP {response.status})")
        return True
    except Exception as e:
        print(f"[BLYNK] V{pin} FAILED: {e}")
        return False


def update_pins(pin_values: dict) -> bool:
    """Update multiple pins one by one."""
    overall_success = True

    for pin, value in pin_values.items():
        ok = update_pin(pin, value)
        if not ok:
            overall_success = False

    return overall_success


def send_sensor_data(data: dict) -> bool:
    """
    Send known sensor fields to Blynk.
    Ignores keys not in PINS.
    """
    pin_values = {}

    for key, pin in PINS.items():
        if key in data and data[key] is not None:
            pin_values[pin] = data[key]

    if not pin_values:
        print("[BLYNK] No matching sensor fields to send")
        return True

    print(f"[BLYNK] Prepared pin payload: {pin_values}")
    return update_pins(pin_values)


def update_property(pin: int, prop: str, value: str) -> bool:
    """Update widget property, e.g. gauge color."""
    if not _has_auth():
        print("[BLYNK] Missing BLYNK_AUTH_TOKEN")
        return False

    params = {"token": BLYNK_AUTH, "pin": f"V{pin}", prop: value}
    url = f"{BLYNK_BASE_URL}/update/property?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            print(f"[BLYNK] Property update V{pin} {prop}={value} OK (HTTP {response.status})")
        return True
    except Exception as e:
        print(f"[BLYNK] Property update V{pin} FAILED: {e}")
        return False


def get_pin(pin: int):
    """Read a virtual pin value from Blynk."""
    if not _has_auth():
        return None
    url = f"{BLYNK_BASE_URL}/get?token={BLYNK_AUTH}&V{pin}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data[0] if data else None
    except Exception as e:
        print(f"[BLYNK] Get V{pin} FAILED: {e}")
        return None


def check_connection() -> bool:
    """Check if Blynk API is reachable."""
    if not _has_auth():
        print("[BLYNK] Missing BLYNK_AUTH_TOKEN")
        return False

    url = f"{BLYNK_BASE_URL}/isHardwareConnected?token={BLYNK_AUTH}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            print(f"[BLYNK] Connection check OK (HTTP {response.status})")
            return response.status == 200
    except Exception as e:
        print(f"[BLYNK] Connection check failed: {e}")
        return False