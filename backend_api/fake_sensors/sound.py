"""
Fake Sound Sensor (Analog Mic via PCF8591)
=======================================
Simulates 8-bit analog sound snapshots.
Normalizes raw 0-255 values to a 0-100 scale.
"""

import random

# Internal state to simulate ambient room noise
_current_raw = 30.0 

def read_sound():
    """
    Simulates analog sound reading on PCF8591 AIN0.
    Returns 0.0 to 100.0 (Silent to Loud).
    """
    global _current_raw

    # 1. Simulate ambient background noise (slight fluctuations)
    # Most analog mics have a small voltage floor even when quiet.
    change = random.uniform(-1.0, 1.0)
    _current_raw += change

    # 2. 2% chance of a loud noise spike (snore, cough, or moving)
    if random.random() < 0.02:
        _current_raw += random.randint(40, 100)

    # 3. Constrain to 8-bit ADC range (0-255)
    _current_raw = max(5.0, min(255.0, _current_raw))

    # 4. Decay logic: return to quiet baseline
    if _current_raw > 35:
        _current_raw -= 2.0

    # 5. Math: Normalize 0-255 to 0-100 (Matches your actual sound.py)
    normalized = round((_current_raw / 255.0) * 100, 1)
    
    return normalized