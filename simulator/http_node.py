import math
import time
from datetime import datetime

import requests


BASE_URL = "http://127.0.0.1:5000"
NODE_ID = "NODE-002"


def sample(counter):
    return {
        "TEMP_001": round(28 + math.sin(counter / 8) * 3, 2),
        "PRESS_001": round(1008 + math.sin(counter / 12) * 4, 2),
        "BATT_V_001": round(4.12 - (counter % 20) * 0.002, 3),
        "BATT_PCT_001": max(0, 92 - (counter % 30)),
        "POWER_001": round(0.6 + math.sin(counter / 5) * 0.2, 3),
        "RSSI_001": -58 + int(math.sin(counter / 6) * 8),
        "SNR_001": round(9 + math.sin(counter / 7) * 2, 1)
    }


def main():
    counter = 0
    while True:
        payload = {
            "node_id": NODE_ID,
            "timestamp": datetime.now().isoformat(),
            "parameters": sample(counter)
        }
        response = requests.post(
            f"{BASE_URL}/api/telemetry",
            json=payload,
            timeout=5
        )
        print(response.status_code, response.text)
        counter += 1
        time.sleep(2)


if __name__ == "__main__":
    main()
