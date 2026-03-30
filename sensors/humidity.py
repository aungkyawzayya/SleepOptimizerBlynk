"""
Fake Humidity Sensor (DHT22 — Sprint 1)
========================================
Simulates bedroom humidity: 30-70%
Inversely related to temperature.

Replace with real DHT22 code:
    import board, adafruit_dht
    dht = adafruit_dht.DHT22(board.D4)
    humidity = dht.humidity
"""

import random

_current = 50.0


def read_humidity():
    """Returns humidity in %."""
    global _current

    change = random.uniform(-0.5, 0.5)
    _current += change
    _current = max(25.0, min(75.0, _current))

    return round(_current, 1)
