import RPi.GPIO as GPIO

FAN_PIN = 18

# Your relay is HIGH-triggered:
# GPIO HIGH = relay ON  = fan ON
# GPIO LOW  = relay OFF = fan OFF

def setup_fan():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(FAN_PIN, GPIO.OUT)
    turn_fan_off()   # ensure safe initial state
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