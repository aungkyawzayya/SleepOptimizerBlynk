"""
Sleep Optimizer — Fake Sensors Package
=======================================
Each sensor has its own module. Import all read functions here.

When you connect real hardware, just replace the fake implementation
inside each file with the real sensor library code.
"""

from sensors.temperature import read_temperature
from sensors.humidity import read_humidity
from sensors.co2 import read_co2
from sensors.sound import read_sound
from sensors.light import read_light
from sensors.dust import read_dust
from sensors.motion import read_motion
from sensors.body_temp import read_body_temp


def read_all():
    """Read all sensors and return as a dict."""
    return {
        'temperature': read_temperature(),
        'humidity': read_humidity(),
        'co2': read_co2(),
        'sound': read_sound(),
        'light': read_light(),
        'dust': read_dust(),
        'motion': read_motion(),
        'body_temp': read_body_temp(),
    }
