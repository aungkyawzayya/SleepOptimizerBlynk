import os

ds18b20 = ""

def setup_temperature():
    """Prepare the sensor data by finding the correct device directory."""
    global ds18b20
    for i in os.listdir('/sys/bus/w1/devices'):
        if i.startswith('28-'):
            ds18b20 = i
            return True
    return False

def read_temperature():
    """get Temperature value from the sensor."""
    if not ds18b20:
        if not setup_temperature():
            return None
            
    try:
        location = f"/sys/bus/w1/devices/{ds18b20}/w1_slave"
        with open(location, 'r') as f:
            lines = f.readlines()
        
        if "YES" not in lines[0]:
            return None

        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            return float(temp_string) / 1000.0
    except Exception as e:
        print(f"Error reading temperature: {e}")
        return None