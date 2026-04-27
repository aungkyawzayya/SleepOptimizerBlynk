import time
try:
    import smbus
except ImportError:
    smbus = None

# Configuration
I2C_ADDR = 0x48
bus = None

def setup_light():
    """Initialize the I2C bus for the light sensor."""
    global bus
    try:
        if smbus:
            bus = smbus.SMBus(1)
            return True
        return False
    except Exception as e:
        print(f"Setup Light Error: {e}")
        return False

def read_light():
    """Read the light intensity value from PCF8591 Channel 2 (AIN2)."""
    global bus
    
    # Ensure setup is done
    if bus is None:
        if not setup_light():
            return 0.0

    try:
        # 0x42 triggers the ADC to read from the third pin (A2)
        bus.write_byte(I2C_ADDR, 0x42) 
        bus.read_byte(I2C_ADDR)           # Flush stale data
        raw_value = bus.read_byte(I2C_ADDR) # Get fresh data

        # Returns a value between 0 (Dark) and 255 (Bright)
        return float(raw_value)

    except Exception as e:
        print(f"Error reading light: {e}")
        return 0.0