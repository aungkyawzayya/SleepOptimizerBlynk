import time
try:
    import smbus
except ImportError:
    smbus = None

# PCF8591 default I2C address
I2C_ADDRESS = 0x48

# We are using Analog Input 0 (A0) on the PCF8591
INPUT_CH0 = 0x40

_bus = None

def setup_sound():
    """Initialize the I2C bus for the PCF8591."""
    global _bus
    if smbus is None:
        print("Warning: smbus library not available. Install with: sudo apt install python3-smbus")
        return False
    try:
        # Use I2C bus 1
        _bus = smbus.SMBus(1)
        # Quick test to see if chip is there
        _bus.write_byte(I2C_ADDRESS, INPUT_CH0)
        print(f"Sound sensor (PCF8591) initialized at I2C address {hex(I2C_ADDRESS)}")
        return True
    except Exception as e:
        print(f"Error setting up PCF8591: {e}")
        return False

def read_sound():
    """
    Reads the analog value from the sound sensor.
    Returns a value between 0.0 and 255.0.
    """
    global _bus
    if _bus is None:
        if not setup_sound():
            return None
    try:
        # The chip needs a 'dummy' read to refresh the internal register
        _bus.write_byte(I2C_ADDRESS, INPUT_CH0)
        _bus.read_byte(I2C_ADDRESS) 
        
        # Now read the actual current sound level
        analog_value = _bus.read_byte(I2C_ADDRESS)
        return float(analog_value)
    except Exception as e:
        print(f"Error reading analog sound sensor: {e}")
        return None