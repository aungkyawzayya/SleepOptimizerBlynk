"""
Sleep Optimizer — Sensor Manager
===================================
Manages the active data-source mode (Raspberry Pi vs Fake API),
maintains sensor history, and runs background tasks for:
  • Polling V15 to detect mode changes
  • Auto-generating fake sensor data when in Fake mode
"""

import asyncio
from datetime import datetime
from collections import deque

import blynk_client


class SensorManager:
    """
    Central store for sensor readings and data-source mode.

    Modes
    -----
    MODE_PI   (0) — Real data posted by Raspberry Pi via /sensors/data.
                    Power button (V12) is active.
    MODE_FAKE (1) — Simulated data auto-generated server-side every
                    FAKE_INTERVAL seconds.
                    Power button (V12) is visually disabled on Blynk.
    """

    MODE_PI   = 0
    MODE_FAKE = 1

    FAKE_INTERVAL = 5   # Initial interval (seconds); overridden at runtime by Blynk V13
    MODE_POLL_INTERVAL = 10  # seconds between V15 reads

    _COLOR_ACTIVE   = "#23C48E"  # Blynk green
    _COLOR_DISABLED = "#808080"  # Blynk grey

    def __init__(self, max_history: int = 100):
        self.mode:        int   = self.MODE_PI
        self.power_on:    bool  = True
        self.interval:    int   = self.FAKE_INTERVAL
        self.latest_data: dict  = {}
        self.history:     deque = deque(maxlen=max_history)

    # ── Mode helpers ──────────────────────────────────────────────

    def is_fake(self) -> bool:
        return self.mode == self.MODE_FAKE

    def set_mode(self, mode: int):
        """Switch data-source mode (Pi / Fake). Does not touch the power button."""
        if mode == self.mode:
            return
        self.mode = mode
        label = "Fake API" if mode == self.MODE_FAKE else "Raspberry Pi"
        print(f"[MODE] Switched to: {label}")

    def set_power(self, on: bool):
        """Turn data collection on or off and sync the Blynk button colour."""
        if on == self.power_on:
            return
        self.power_on = on
        print(f"[POWER] {'ON' if on else 'OFF'}")
        try:
            color = self._COLOR_ACTIVE if on else self._COLOR_DISABLED
            blynk_client.update_property(
                blynk_client.PINS['power'], "color", color)
        except Exception as e:
            print(f"[POWER UI ERROR] {e}")

    # ── Data processing ───────────────────────────────────────────

    def process(self, data: dict, save_fn=None) -> dict:
        """
        Record a sensor reading, persist to DB (optional), sync to Blynk.

        Args:
            data:    Sensor dict
            save_fn: Optional callable(data) for DB persistence

        Returns:
            API response dict
        """
        self.latest_data = data
        self.history.append({**data, "timestamp": datetime.now().strftime("%H:%M:%S")})

        if save_fn:
            save_fn(data)

        ok = blynk_client.send_sensor_data(data)
        return {"status": "success", "blynk": "ok" if ok else "failed", "data": data}

    # ── Background tasks ──────────────────────────────────────────

    async def poll_mode(self):
        """
        Background task: read V15 (mode) and V12 (power) every
        MODE_POLL_INTERVAL seconds. Switches state automatically
        when either Blynk widget changes.
        """
        def _poll_blynk():
            val = blynk_client.get_pin(blynk_client.PINS['data_source'])
            if val is not None:
                self.set_mode(int(float(val)))

            pwr = blynk_client.get_pin(blynk_client.PINS['power'])
            if pwr is not None:
                self.set_power(bool(int(float(pwr))))

            interv = blynk_client.get_pin(blynk_client.PINS['interval'])
            if interv is not None:
                self.interval = max(5, min(300, int(float(interv))))

        while True:
            try:
                await asyncio.to_thread(_poll_blynk)
            except Exception as e:
                print(f"[POLL ERROR] {e}")
            await asyncio.sleep(self.MODE_POLL_INTERVAL)

    async def fake_data_loop(self):
        """
        Background task: auto-generate fake sensor readings every
        FAKE_INTERVAL seconds — but only when in Fake mode.
        Idles silently when in Pi mode.
        """
        from fake_sensors import read_all
        while True:
            if self.is_fake() and self.power_on:
                try:
                    data = read_all()
                    await asyncio.to_thread(self.process, data)
                    print(f"[FAKE] Auto sensor tick (interval: {self.interval}s)")
                except Exception as e:
                    print(f"[FAKE ERROR] {e}")
            await asyncio.sleep(self.interval)
