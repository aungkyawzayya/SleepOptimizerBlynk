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
        _bus = smbus.SMBus(1)
        _bus.write_byte(I2C_ADDRESS, INPUT_CH0)
        print(f"Sound sensor (PCF8591) initialized at I2C address {hex(I2C_ADDRESS)}")
        return True
    except Exception as e:
        print(f"Error setting up PCF8591: {e}")
        return False

def read_sound():
    """
    Reads analog value from PCF8591 and normalizes to 0-100.
    0 = silent, 100 = very loud.
    """
    global _bus
    if _bus is None:
        if not setup_sound():
            return None
    try:
        # Dummy read to refresh internal register
        _bus.write_byte(I2C_ADDRESS, INPUT_CH0)
        _bus.read_byte(I2C_ADDRESS)

        # Actual read
        analog_value = _bus.read_byte(I2C_ADDRESS)
       
        return analog_value
    except Exception as e:
        print(f"Error reading sound sensor: {e}")
        return None