"""Offline calibration arithmetic; requires measured circuit and gas-specific reference. Never writes a device."""
import argparse,json,math

def calculate(pin_mv,divider_gain,supply_mv,rl_ohms,reference_ppm,curve_a,curve_b):
 values=(pin_mv,divider_gain,supply_mv,rl_ohms,reference_ppm,curve_a,curve_b)
 if not all(math.isfinite(v) for v in values) or min(values[:-1])<=0 or divider_gain<1 or curve_b==0:raise ValueError('Measured positive values and a nonzero gas-curve slope are required')
 ao=pin_mv*divider_gain
 if ao>=supply_mv or pin_mv>3300:raise ValueError('Measurement outside divider/supply limits')
 rs=rl_ohms*(supply_mv/ao-1)
 ratio=(reference_ppm/curve_a)**(1/curve_b)
 return {'rs_ohms':rs,'r0_ohms':rs/ratio,'reference_ppm':reference_ppm,'basis':'USER_SUPPLIED_MEASURED_REFERENCE','device_settings_written':False,'warning':'This arithmetic does not validate the sensor, gas selectivity, reference instrument or calibration curve.'}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('pin-mv','divider-gain','supply-mv','rl-ohms','reference-ppm','curve-a','curve-b'):p.add_argument('--'+name,type=float,required=True)
 a=p.parse_args();print(json.dumps(calculate(a.pin_mv,a.divider_gain,a.supply_mv,a.rl_ohms,a.reference_ppm,a.curve_a,a.curve_b),indent=2))
