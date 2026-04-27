import time
try:
    import smbus
except ImportError:
    smbus = None

# Configuration
I2C_ADDR = 0x48
bus = None

def setup_light():
    """Initialize the I2C bus safely."""
    global bus
    if smbus is None:
        return False
    try:
        bus = smbus.SMBus(1)
        return True
    except Exception as e:
        print(f"Setup Light Error: {e}")
        return False

def read_light():
    """Read and invert light level from Channel A2."""
    global bus
    
    if bus is None:
        if not setup_light():
            return 0 # Fallback if no hardware is found

    try:
        # 0x42 targets the A2 pin on the PCF8591
        bus.write_byte(I2C_ADDR, 0x42)
        bus.read_byte(I2C_ADDR)           # Flush stale data
        raw_value = bus.read_byte(I2C_ADDR) # Get fresh value
        
        # Inversion: 255 (Max) - raw (Sensor Reading)
        # This makes the result: Higher Number = Brighter
        corrected_light = 255 - raw_value
        
        return corrected_light
    except Exception as e:
        return 0