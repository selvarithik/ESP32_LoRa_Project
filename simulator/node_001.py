import random
import time
import json
import sys
import os
import socketio

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from protocol.messages import create_telemetry


NODE_ID = "NODE-001"
FIRMWARE = "v1.0.0"

packets_tx = 0
packets_rx = 0

start_time = time.time()
battery_voltage = 4.15


# Connect to Gateway Backend
sio = socketio.Client()

print(f"{NODE_ID}: Connecting to gateway...")

sio.connect("http://127.0.0.1:5000")

print(f"{NODE_ID}: Connected to gateway.")


while True:

    uptime = int(time.time() - start_time)

    temperature = 29.0 + random.uniform(-1.0, 1.0)
    humidity = 60.0 + random.uniform(-3.0, 3.0)

    current_ma = 80 + random.uniform(-10, 15)

    battery_voltage -= 0.0002
    battery_voltage = max(battery_voltage, 3.30)

    battery_percent = (
        (battery_voltage - 3.30)
        / (4.20 - 3.30)
        * 100
    )

    rssi = -70 + random.uniform(-6, 6)
    snr = 9 + random.uniform(-2, 2)

    packets_tx += 1

    if random.random() > 0.02:
        packets_rx += 1

    data = create_telemetry(
        node_id=NODE_ID,
        temperature=temperature,
        humidity=humidity,
        battery_voltage=battery_voltage,
        battery_percent=battery_percent,
        current_ma=current_ma,
        rssi=rssi,
        snr=snr,
        packets_tx=packets_tx,
        packets_rx=packets_rx,
        firmware=FIRMWARE,
        uptime=uptime
    )

    # Send telemetry to backend
    sio.emit("telemetry", data)

    # Also show data in terminal
    print(json.dumps(data))

    time.sleep(2)