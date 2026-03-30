"""
Fake Temperature Sensor (DHT22 — Sprint 1)
============================================
Simulates bedroom temperature: 17-28°C
Cooler at night, warmer during day.

Replace with real DHT22 code:
    import board, adafruit_dht
    dht = adafruit_dht.DHT22(board.D4)
    temperature = dht.temperature
"""

import random
from datetime import datetime

_current = 22.0


def _is_night():
    hour = datetime.now().hour
    return hour >= 22 or hour < 7


def read_temperature():
    """Returns temperature in °C."""
    global _current

    change = random.uniform(-0.3, 0.3)
    _current += change

    if _is_night():
        _current = max(17.0, min(23.0, _current))
    else:
        _current = max(20.0, min(28.0, _current))

    return round(_current, 1)
