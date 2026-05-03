"""
Fake PIR Motion Sensor (Digital Input)
=======================================
Simulates binary 1/0 motion detection.
Higher probability of motion during 'transition' hours 
(going to bed/waking up) and very low during deep sleep.
"""

import random
from datetime import datetime

def _is_sleep_time():
    hour = datetime.now().hour
    # Deep sleep: 11 PM to 6 AM
    return 23 <= hour or hour < 6

def _is_transition_time():
    hour = datetime.now().hour
    # Getting ready for bed (10 PM) or waking up (6-8 AM)
    return hour == 22 or (6 <= hour < 8)

def read_motion():
    """
    Simulates digital PIR on BCM Pin 23.
    Returns 1 (Motion) or 0 (Still).
    """
    chance = random.random()

    if _is_transition_time():
        # 30% chance of motion while moving around the room
        is_detected = 1 if chance < 0.30 else 0
    elif _is_sleep_time():
        # 3% chance of motion (tossing/turning in sleep)
        is_detected = 1 if chance < 0.03 else 0
    else:
        # Daytime: 10% chance (empty room, occasional movement)
        is_detected = 1 if chance < 0.10 else 0

    return is_detected