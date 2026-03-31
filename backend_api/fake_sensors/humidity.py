"""
Fake Humidity Sensor (DHT22 — Sprint 1)
========================================
Simulates bedroom humidity: 30-70%
Inversely related to temperature.
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
