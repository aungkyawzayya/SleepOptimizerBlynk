"""
Fake Dust/Air Quality Sensor (PMS5003 — Sprint 5)
===================================================
Simulates PM2.5 levels: 5-25 µg/m³ baseline
Occasional spikes when someone moves or fan turns on.

Replace with real PMS5003 code:
    from pms5003 import PMS5003
    pms = PMS5003()
    data = pms.read()
    pm25 = data.pm_ug_per_m3(2.5)
"""

import random

_current = 8.0


def read_dust():
    """Returns PM2.5 in µg/m³."""
    global _current

    change = random.uniform(-0.5, 0.5)
    _current += change

    # 3% chance of dust spike
    if random.random() < 0.03:
        _current += random.uniform(10, 30)

    # Decay back to baseline after spike
    if _current > 25:
        _current -= random.uniform(1, 3)

    _current = max(0.0, min(100.0, _current))

    return round(_current, 1)
