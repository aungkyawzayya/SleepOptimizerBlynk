import RPi.GPIO as GPIO
import time

FAN_PIN = 18

# HIGH-triggered relay:
# GPIO HIGH = fan ON
# GPIO LOW  = fan OFF

def setup_fan():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # 🔥 VERY IMPORTANT: set initial state BEFORE enabling output
    GPIO.setup(FAN_PIN, GPIO.OUT, initial=GPIO.LOW)

    # small delay to stabilize relay (optional but recommended)
    time.sleep(0.1)

    return True


def turn_fan_on():
    GPIO.output(FAN_PIN, GPIO.HIGH)


def turn_fan_off():
    GPIO.output(FAN_PIN, GPIO.LOW)


def set_fan(state: int):
    if state == 1:
        turn_fan_on()
    else:
        turn_fan_off()


def cleanup_fan():
    turn_fan_off()
    GPIO.cleanup(FAN_PIN)