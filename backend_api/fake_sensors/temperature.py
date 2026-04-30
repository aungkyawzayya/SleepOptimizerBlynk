"""
Fake Temperature Sensor (DHT22 — Sprint 1)
============================================
Simulates realistic bedroom thermal drift.
Baseline: 17-28°C (Cooler at night).
"""

import random
from datetime import datetime

# Starting baseline
_current_temp = 22.0

def _is_night():
    """Determines if the simulation should use nighttime cooling."""
    hour = datetime.now().hour
    return hour >= 22 or hour < 7

def read_temperature():
    """
    Returns temperature in °C.
    Simulates the behavior of a DHT22 sensor.
    """
    global _current_temp

    # Small fluctuations to simulate air movement
    change = random.uniform(-0.15, 0.15)
    _current_temp += change

    # Boundary logic based on time of day
    if _is_night():
        # Night: Slowly drift toward a cooler range
        if _current_temp > 20.0:
            _current_temp -= 0.05
        _current_temp = max(17.0, min(23.0, _current_temp))
    else:
        # Day: Slowly drift toward a warmer range
        if _current_temp < 23.0:
            _current_temp += 0.05
        _current_temp = max(20.0, min(28.0, _current_temp))

    return round(_current_temp, 1)