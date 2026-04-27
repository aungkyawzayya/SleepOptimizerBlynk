import smbus

I2C_ADDR = 0x48
bus = None

def setup_light():
    """Initialize the I2C bus for the light sensor."""
    global bus
    try:
        bus = smbus.SMBus(1)
        return True
    except Exception as e:
        print(f"Setup Light Error: {e}")
        return False

def read_light():
    """Read the analog light level from AIN2."""
    global bus
    if bus is None:
        if not setup_light():
            return 0
    try:
        # 0x42 tells the PCF8591 to read from the A2 pin
        bus.write_byte(I2C_ADDR, 0x42)
        bus.read_byte(I2C_ADDR)           # Flush old data
        raw_value = bus.read_byte(I2C_ADDR) # Get fresh light level
        
        # Returns 0 (Dark) to 255 (Very Bright)
        return raw_value
    except Exception as e:
        print(f"Error reading light: {e}")
        return 0