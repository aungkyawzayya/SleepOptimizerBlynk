"""
Sleep Optimizer — Fake Sensors Package
=======================================
Simulated sensor data for testing without real hardware.
"""

from .temperature import read_temperature
from .sound import read_sound
from .light import read_light
from .motion import read_motion
from .dust import read_dust

def read_all():
    """Read available fake sensors and return as a dict."""
    return {
        'temperature': read_temperature(),
        'sound': read_sound(),
        'light': read_light(),
        'dust': read_dust(),
        'motion': read_motion(),
    }