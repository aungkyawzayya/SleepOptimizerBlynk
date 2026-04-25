import smbus
import time

# I2C address of the PCF8591 is usually 0x48
address = 0x48

# Initialize I2C bus
bus = smbus.SMBus(1)

def setup_sound():
    """
    For the PCF8591, 'setup' just means checking if the 
    chip is responding on the I2C bus.
    """
    try:
        # Quick write to test connection
        bus.write_byte(address, 0x40)
        print(f"PCF8591 found at address {hex(address)}")
        return True
    except Exception as e:
        print(f"Error connecting to PCF8591: {e}")
        return False

def read_sound():
    """
    Reads the analog value from Channel 0 (where your Yellow wire is).
    Returns a value between 0 and 255.
    """
    try:
        # 0x40 tells the chip to read Analog Input 0 (A0)
        bus.write_byte(address, 0x40)
        
        # The first read often returns the 'previous' value, 
        # so we read twice to get the current sound level.
        bus.read_byte(address) 
        value = bus.read_byte(address)
        
        return value
    except Exception as e:
        print(f"Error reading sound: {e}")
        return None

# --- Testing the code ---
if setup_sound():
    print("Speak into the microphone to see the numbers change...")
    try:
        while True:
            sound_level = read_sound()
            if sound_level is not None:
                # This will print numbers (e.g., 120, 150, 200)
                print(f"Current Sound Level: {sound_level}")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("Stopping...")