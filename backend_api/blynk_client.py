def get_pin(pin: int):
    """Read a virtual pin value from Blynk safely."""
    if not _has_auth():
        return None
    
    # Updated URL format to match Blynk's latest GET API
    url = f"{BLYNK_BASE_URL}/get?token={BLYNK_AUTH}&V{pin}"
    
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            raw_data = response.read().decode()
            data = json.loads(raw_data)
            
            # If Blynk returns ["1"], return "1"
            if isinstance(data, list):
                return data[0] if data else None
            
            # If Blynk returns 1 (raw int/string), return it directly
            return data
            
    except Exception as e:
        print(f"[BLYNK] Get V{pin} FAILED: {e}")
        return None