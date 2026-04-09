"""
Sleep Optimizer — Fake Sensors Package
=======================================
Simulated sensor data for testing without real hardware.
"""

from .temperature import read_temperature
from .humidity import read_humidity
from .co2 import read_co2
from .sound import read_sound
from .light import read_light
from .motion import read_motion
from .dust import read_dust

def read_all():
    """Read available fake sensors and return as a dict."""
    return {
        'temperature': read_temperature(),
        'humidity': read_humidity(),
        'co2': read_co2(),
        'sound': read_sound(),
        'light': read_light(),
        'dust': read_dust(),
        'motion': read_motion(),
    }