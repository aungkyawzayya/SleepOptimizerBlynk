import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

# Configuration
PIR_PIN = 23
is_setup = False  # Acts like the 'bus' variable in light.py to track state

def setup_motion():
    """Initialize the GPIO pins safely."""
    global is_setup
    
    if GPIO is None:
        return False
        
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        # We keep the PUD_DOWN fix here to prevent floating 1s
        GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        is_setup = True
        return True
    except Exception as e:
        print(f"Setup Motion Error: {e}")
        return False

def read_motion():
    """Read the motion sensor, returning 0 if hardware is missing."""
    global is_setup
    
    # Try to initialize if it hasn't been done yet
    if not is_setup:
        if not setup_motion():
            return 0  # Fallback if no hardware is found

    try:
        # Read the actual pin (returns 1 for motion, 0 for still)
        motion_value = GPIO.input(PIR_PIN)
        return motion_value
    except Exception as e:
        # If the read fails for any reason, safely return 0
        return 0