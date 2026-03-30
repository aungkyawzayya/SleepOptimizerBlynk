"""
Fake Motion Sensor (HC-SR501 — Sprint 6)
==========================================
Simulates PIR motion detection: 0 or 1
8% chance at night (tossing in sleep), 30% during day.

Replace with real HC-SR501 code:
    import RPi.GPIO as GPIO
    GPIO.setup(17, GPIO.IN)
    motion = GPIO.input(17)
"""

import random
from datetime import datetime


def _is_night():
    hour = datetime.now().hour
    return hour >= 22 or hour < 7


def read_motion():
    """Returns 1 if motion detected, 0 otherwise."""
    if _is_night():
        return 1 if random.random() < 0.08 else 0
    else:
        return 1 if random.random() < 0.30 else 0
