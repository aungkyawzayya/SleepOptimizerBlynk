import time
try:
    import smbus
except ImportError:
    smbus = None
import RPi.GPIO as GPIO

# Configuration
I2C_ADDR = 0x48
LED_PIN = 24  # Green wire (Signal D) connected to GPIO 24
bus = None

def setup_dust():
    """Initialize GPIO and the I2C bus for the dust sensor."""
    global bus
    try:
        # GPIO setup for the LED trigger
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.output(LED_PIN, GPIO.HIGH) # Keep LED off initially

        # Initialize I2C bus
        bus = smbus.SMBus(1)
        return True
    except Exception as e:
        print(f"Setup Dust Error: {e}")
        return False

def read_dust():
    """Calculate dust density by pulsing the LED and reading AIN1."""
    global bus
    
    # Ensure setup is done
    if bus is None:
        if not setup_dust():
            return 0.0

    try:
        # 1. Pulse the LED ON
        GPIO.output(LED_PIN, GPIO.LOW)
        time.sleep(0.00028) # 0.28ms delay required by datasheet

        # 2. Read from PCF8591 Channel 1 (AIN1)
        # 0x41 triggers the ADC to read from the second pin (A1)
        bus.write_byte(I2C_ADDR, 0x41) 
        bus.read_byte(I2C_ADDR)           # Flush stale data
        raw_value = bus.read_byte(I2C_ADDR) # Get fresh data

        # 3. Pulse the LED OFF
        time.sleep(0.00004)
        GPIO.output(LED_PIN, GPIO.HIGH)
        
        # 4. Convert 8-bit value (0-255) to Voltage and Density
        voltage = (raw_value * 3.3) / 255.0
        
        # Standard linear equation for Sharp GP2Y1010AU0F
        dust_density = 0.17 * voltage - 0.1
        
        # Avoid negative values in clean air
        if dust_density < 0:
            dust_density = 0.0
            
        return round(dust_density, 4)

    except Exception as e:
        print(f"Error reading dust: {e}")
        return 0.0