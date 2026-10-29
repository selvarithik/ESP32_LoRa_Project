# MQ-135 calibration assessment — 29 October 2026

Current output remains raw ADC counts and GPIO pin millivolts, not calibrated ppm or an official air-quality index. No sensor setting or fabricated reference value was applied.

Manufacturer reference: https://www.winsen-sensor.com/manual/mq135.html and the linked MQ135 Version 1.6 manual. It specifies a 5 V heater and more than 48 hours initial preheating. It responds to multiple gases, including ammonia, sulfides, benzene-series vapours, hydrogen and smoke. An internet outdoor CO2 value is not a known concentration at this sensor and cannot calibrate it.

Before a defensible concentration estimate: identify the actual module load resistance RL, measured sensor circuit voltage and ADC divider ratio; complete manufacturer preheating; measure a clean/reference atmosphere under known temperature/humidity; obtain calibration points for the intended target gas. DHT11 is currently faulty, so environmental compensation cannot be verified. Do not expose people or this prototype to test gas deliberately.

For a verified basic resistive circuit, Rs=(Vc/VRL-1)*RL; VRL is the original sensor output voltage, not the reduced ESP32 ADC pin voltage. A divider can load the module output and must be accounted for. Use the curve and R0 definition from the exact sensor manual, not an arbitrary library constant. Cross-sensitivity prevents identifying a gas uniquely from one measurement.

The saved project warm-up setting was preserved; it does not prove the manufacturer's initial preheat requirement was met. Raw trends may indicate a changing sensor response, but no Good/Poor/Safe air label, ppm concentration or AQI is justified yet. Exact pending actions: measured RL/circuit/divider values, verified warm-up, a suitable known reference and target-gas validation.
