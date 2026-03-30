"""
Fake Sound Sensor (MAX4466 — Sprint 3)
========================================
Simulates bedroom noise: 20-45dB baseline
Occasional spikes for snoring or traffic.

Replace with real MAX4466 code:
    import analogio
    mic = analogio.AnalogIn(board.A0)
    # Convert analog reading to dB
"""

import random

_current = 25.0


def read_sound():
    """Returns sound level in dB."""
    global _current

    change = random.uniform(-1.0, 1.0)
    _current += change

    # 5% chance of noise spike (snoring, traffic)
    if random.random() < 0.05:
        _current += random.uniform(15, 40)

    _current = max(15.0, min(90.0, _current))

    # Decay back to baseline after spike
    if _current > 40:
        _current -= random.uniform(2, 5)

    return round(_current, 1)
