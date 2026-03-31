"""
Sleep Optimizer — Fake Sensors Package
=======================================
Simulated sensor data for testing without real hardware.
Each sensor generates realistic random values.
"""

from fake_sensors.temperature import read_temperature
from fake_sensors.humidity import read_humidity
from fake_sensors.co2 import read_co2
from fake_sensors.sound import read_sound
from fake_sensors.light import read_light
from fake_sensors.dust import read_dust
from fake_sensors.motion import read_motion
from fake_sensors.body_temp import read_body_temp


def read_all():
    """Read all fake sensors and return as a dict."""
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