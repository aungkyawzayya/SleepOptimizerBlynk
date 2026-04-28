import RPi.GPIO as GPIO

FAN_PIN = 18

# Most relay modules are LOW-triggered:
# GPIO LOW  = relay ON  = fan ON
# GPIO HIGH = relay OFF = fan OFF

def setup_fan():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(FAN_PIN, GPIO.OUT)
    turn_fan_off()
    return True


def turn_fan_on():
    GPIO.output(FAN_PIN, GPIO.LOW)


def turn_fan_off():
    GPIO.output(FAN_PIN, GPIO.HIGH)


def set_fan(state: int):
    if state == 1:
        turn_fan_on()
    else:
        turn_fan_off()


def cleanup_fan():
    turn_fan_off()
    GPIO.cleanup(FAN_PIN)