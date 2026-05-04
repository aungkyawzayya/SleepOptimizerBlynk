import RPi.GPIO as GPIO

PIR_PIN = 23

def setup_motion():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIR_PIN, GPIO.IN)
    return True

def read_motion():
    return GPIO.input(PIR_PIN)