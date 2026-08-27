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


NODE_ID = "NODE-002"
FIRMWARE = "v1.0.0"

packets_tx = 0
packets_rx = 0

start_time = time.time()
battery_voltage = 4.05


# Connect to Gateway Backend
sio = socketio.Client()

print(f"{NODE_ID}: Connecting to gateway...")

sio.connect("http://127.0.0.1:5000")

print(f"{NODE_ID}: Connected to gateway.")


while True:

    uptime = int(time.time() - start_time)

    temperature = 30.0 + random.uniform(-1.2, 1.2)
    humidity = 57.0 + random.uniform(-4, 4)

    current_ma = 95 + random.uniform(-12, 15)

    battery_voltage -= 0.00015
    battery_voltage = max(battery_voltage, 3.30)

    battery_percent = (
        (battery_voltage - 3.30)
        / (4.20 - 3.30)
        * 100
    )

    rssi = -78 + random.uniform(-5, 5)
    snr = 7 + random.uniform(-2, 2)

    packets_tx += 1

    if random.random() > 0.03:
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