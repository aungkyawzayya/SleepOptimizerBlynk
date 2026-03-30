"""
Fake Body Temperature Sensor (MLX90614 — Sprint 7)
====================================================
Simulates contactless body temp: 36.1-37.2°C
Very stable with tiny variations.

Replace with real MLX90614 code:
    import smbus2
    from mlx90614 import MLX90614
    sensor = MLX90614(smbus2.SMBus(1))
    body_temp = sensor.get_object_1()
"""

import random

_current = 36.5


def read_body_temp():
    """Returns body temperature in °C."""
    global _current

    change = random.uniform(-0.05, 0.05)
    _current += change
    _current = max(36.1, min(37.2, _current))

    return round(_current, 1)
