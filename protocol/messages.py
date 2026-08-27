from datetime import datetime


def create_telemetry(
    node_id,
    temperature,
    humidity,
    battery_voltage,
    battery_percent,
    current_ma,
    rssi,
    snr,
    packets_tx,
    packets_rx,
    firmware,
    uptime
):
    return {
        "type": "telemetry",
        "timestamp": datetime.now().isoformat(),

        "node_id": node_id,

        "sensor": {
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1)
        },

        "battery": {
            "voltage": round(battery_voltage, 2),
            "percent": round(battery_percent, 1),
            "current_ma": round(current_ma, 1),
            "power_mw": round(
                battery_voltage * current_ma,
                1
            )
        },

        "lora": {
            "rssi": round(rssi, 1),
            "snr": round(snr, 1),
            "packets_tx": packets_tx,
            "packets_rx": packets_rx
        },

        "device": {
            "firmware": firmware,
            "uptime": uptime,
            "status": "online"
        }
    }