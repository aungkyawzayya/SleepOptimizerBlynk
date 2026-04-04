import time
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

SOUND_PIN = 27  # BCM pin number — update if wired differently

_is_setup = False


def setup_sound():
    """Initialize the sound sensor GPIO pin."""
    global _is_setup
    if GPIO is None:
        print("Warning: RPi.GPIO not available")
        return False
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SOUND_PIN, GPIO.IN)
        _is_setup = True
        print(f"Sound sensor initialized on GPIO {SOUND_PIN}")
        return True
    except Exception as e:
        print(f"Error setting up sound sensor: {e}")
        return False


def read_sound():
    """
    Sample the digital sound sensor 10 times over 0.5s.
    Returns 1.0 if sound was detected in any sample, 0.0 if quiet.
    """
    global _is_setup
    if GPIO is None:
        return None
    if not _is_setup:
        if not setup_sound():
            return None
    try:
        detections = 0
        samples = 10
        for _ in range(samples):
            if GPIO.input(SOUND_PIN):
                detections += 1
            time.sleep(0.05)  # 0.5s total sampling window
        return 1.0 if detections > 0 else 0.0
    except Exception as e:
        print(f"Error reading sound sensor: {e}")
        return None
