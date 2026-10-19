"""Device controls reuse authenticated command endpoints, never proxy secrets to devices."""
from flask import render_template,jsonify
import device_api
import device_control_contract as contract
import node_manager

def install(app):
 @app.get('/device-controls')
 @device_api.require_admin
 def device_controls_page():return render_template('device_controls.html')
 @app.get('/api/device-controls')
 @device_api.require_admin
 def device_controls_catalog():
  return jsonify(schema_version=1,commands=sorted(contract.COMMANDS),fields={k:dict(type=v[0],minimum=v[1],maximum=v[2]) for k,v in contract.FIELDS.items()},interval_presets=[2,5,10,30,60],nodes=[n for n in node_manager.get_all_nodes() if n.get('device_enrolled')],credentials='PHYSICAL_USB_ONLY',radio='DRIVER_UNAVAILABLE_UNTIL_HARDWARE_VERIFIED')
