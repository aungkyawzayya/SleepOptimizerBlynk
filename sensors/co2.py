"""
Fake CO₂ Sensor (MH-Z19B — Sprint 2)
======================================
Simulates bedroom CO₂: 400-1200ppm
Rises gradually at night (closed room), drops during day.

Replace with real MH-Z19B code:
    import mh_z19
    co2 = mh_z19.read_all()['co2']
"""

import random
from datetime import datetime

_current = 450.0


def _is_night():
    hour = datetime.now().hour
    return hour >= 22 or hour < 7


def read_co2():
    """Returns CO₂ in ppm."""
    global _current

    change = random.uniform(-5, 5)
    _current += change

    if _is_night():
        _current += random.uniform(0, 2)  # rising trend
        _current = max(400, min(1200, _current))
    else:
        _current -= random.uniform(0, 3)  # dropping trend
        _current = max(380, min(800, _current))

    return int(round(_current))
