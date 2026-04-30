"""
Fake Dust Sensor (Sharp GP2Y1010AU0F via PCF8591)
===================================================
Simulates raw 8-bit ADC readings (0-255) and converts 
to mg/m³ using the standard linear equation.
"""

import random

# Global to track state for smooth transitions
_raw_value = 40.0 

def read_dust():
    """
    Simulates the Sharp GP2Y1010AU0F logic on a 3.3V Raspberry Pi.
    Returns: float (dust density in mg/m3)
    """
    global _raw_value

    # 1. Simulate minor raw fluctuations (-2 to +2 steps on the ADC)
    change = random.uniform(-2, 2)
    _raw_value += change

    # 2. Occasional 5% chance of a "Dust Spike" (e.g., someone walking by)
    if random.random() < 0.05:
        _raw_value += random.randint(30, 60)

    # 3. Constrain to 8-bit range (0-255)
    _raw_value = max(0.0, min(255.0, _raw_value))
    
    # 4. Math: Convert raw ADC to Voltage (assuming 3.3V Ref)
    #
    voltage = (_raw_value * 3.3) / 255.0
    
    # 5. Math: Convert Voltage to mg/m3
    # Equation: 0.17 * voltage - 0.1
    dust_density = 0.17 * voltage - 0.1
    
    # 6. Decay logic: slowly return to baseline (~0.03 mg/m3)
    if _raw_value > 40:
        _raw_value -= 1.5

    return round(max(0.0, dust_density), 4)