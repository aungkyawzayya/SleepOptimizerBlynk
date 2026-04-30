"""
Fake Light Sensor (LDR via PCF8591)
=======================================
Simulates 8-bit analog light levels: 
Low raw value = Bright / High raw value = Dark.
Returns inverted 0-255 (Higher = Brighter).
"""

import random
from datetime import datetime

# Internal raw ADC state (0-255)
# In a real LDR circuit, raw value is HIGH when it's dark.
_raw_adc = 200.0 

def _is_night():
    hour = datetime.now().hour
    # Night is between 10 PM and 7 AM
    return hour >= 22 or hour < 7

def read_light():
    """
    Simulates LDR on PCF8591 Channel A2.
    Returns 0-255 (Higher Number = Brighter Room).
    """
    global _raw_adc

    if _is_night():
        # Night: Raw ADC value is high (high resistance)
        # We simulate a raw value between 200 and 250
        _raw_adc = random.uniform(200.0, 250.0)
    else:
        # Day: Raw ADC value is lower (low resistance)
        # We simulate a raw value between 20 and 100
        _raw_adc = random.uniform(20.0, 100.0)

    # Apply the exact inversion logic from your real code:
    # This makes 255 = Very Bright and 0 = Total Darkness
    corrected_light = 255 - _raw_adc
    
    return int(max(0, min(255, corrected_light)))