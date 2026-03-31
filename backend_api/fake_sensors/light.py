"""
Fake Light Sensor (BH1750 — Sprint 4)
=======================================
Simulates bedroom light: 0 lux at night, 50-500 lux during day.
"""

import random
from datetime import datetime

_current = 5.0


def _is_night():
    hour = datetime.now().hour
    return hour >= 22 or hour < 7


def read_light():
    """Returns light level in lux."""
    global _current

    if _is_night():
        change = random.uniform(-0.5, 0.5)
        _current += change
        _current = max(0.0, min(5.0, _current))
    else:
        change = random.uniform(-10.0, 10.0)
        _current += change
        _current = max(50.0, min(500.0, _current))

    return round(_current, 1)
