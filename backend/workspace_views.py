"""Read-only workspace projections. Saved roles/parent IDs are not RF observations."""
import json
from datetime import datetime
from flask import jsonify,render_template
import database
import device_api
import mqtt_api
import local_ip

NAVIGATION=[{'label':'Dashboard','path':'/'},{'label':'Device Management','path':'/nodes'},{'label':'Sensor Management','path':'/sensors'},
 {'label':'Communication','children':[{'label':'LoRa Mesh Monitor','path':'/communication'},{'label':'MQTT Setup & Testing','path':'/mqtt'},{'label':'Network & Communication','path':'/network'}]},
 {'label':'Command Center','path':'/command-center'},{'label':'Diagnostics','path':'/diagnostics'},
 {'label':'System','children':[{'label':'Health','path':'/system-overview'},{'label':'Master / Node Controls','path':'/device-controls'},{'label':'Local IP Communication','path':'/local-ip'}]},
 {'label':'Settings','path':'/system'},{'label':'Existing tools','children':[{'label':'Firmware','path':'/firmware'},{'label':'Private Chat','path':'/chat'}]}]

def overview():
    db=database.get_connection()
    try:
        rows=db.execute('SELECT * FROM nodes WHERE device_enrolled=1 ORDER BY device_role,node_id').fetchall()
        devices=[]
        for row in rows:
            try:reported=json.loads(row['latest_status'] or '{}')
            except (ValueError,TypeError):reported={}
            if not isinstance(reported,dict):reported={}
            prepared=dict(row);prepared['latest_status']=json.dumps(reported);public=device_api.public_node(prepared)
            # Allowlist projections: never include a stored configuration or arbitrary diagnostic payload.
            device={key:public.get(key) for key in ('node_id','name','device_role','master_id','hardware_mac','firmware_version','last_seen','health','enabled','node_address')}
            fields=('device_name','hardware_mac','firmware_version','wifi_connected','wifi_rssi','gateway_reachable','transport','internet_status','uptime_s','telemetry_seconds','sensor_status')
            device['reported']={key:reported.get(key) if type(reported.get(key)) in (str,int,float,bool,type(None)) else None for key in fields}
            device['diagnostics']={}
            for kind in ('GET_NETWORK','GET_RADIO_STATUS','GET_MESH_STATUS','GET_ROUTE_INFO'):
                command=db.execute("SELECT result,response_at FROM commands WHERE node_id=? AND command_type=? AND state='COMPLETED' ORDER BY response_at DESC LIMIT 1",(row['node_id'],kind)).fetchone()
                if not command:continue
                try:value=json.loads(command['result'] or '{}')
                except (ValueError,TypeError):continue
                allowed={'GET_NETWORK':('connected','station_ip','ip','rssi','dhcp','subnet','gateway','dns','disconnect_reason','reconnect_attempts'),'GET_RADIO_STATUS':('state','error','public_settings_read','register_writes','rx_messages','tx_uart_fragments','rejected','auth_failures','timeouts','observed','hardware_link_verified'),'GET_MESH_STATUS':('radio_state','hardware_verified','node_count','route_count','pending','delivery_failures','duplicates'),'GET_ROUTE_INFO':('radio_state','hardware_verified','routes')}[kind]
                if isinstance(value,dict):
                    projected={key:value.get(key) for key in allowed if key in value and (key in ('observed','routes') or type(value.get(key)) in (str,int,float,bool,type(None)))}
                    if 'observed' in projected:
                        observed=projected['observed'];projected['observed']={key:observed[key] for key in ('address','baud','channel','air_rate_code','power_dbm','subpacket_bytes','fixed_mode','rssi_enabled','lbt') if isinstance(observed,dict) and key in observed and type(observed[key]) in (str,int,float,bool,type(None))}
                    if 'routes' in projected:
                        projected['routes']=[{key:route[key] for key in ('destination','next_hop','hop_count','age_ms') if key in route and type(route[key]) in (str,int,float,bool,type(None))} for route in projected['routes'][:12] if isinstance(route,dict)] if isinstance(projected['routes'],list) else []
                    device['diagnostics'][kind]={'received_at':command['response_at'],'data':projected}
            devices.append(device)
    finally:db.close()
    masters=[d for d in devices if d['device_role']=='MASTER'];nodes=[d for d in devices if d['device_role']=='NODE']
    mqtt=mqtt_api.service().status();listener=local_ip.service.status()
    return {'observed_at':datetime.now().isoformat(),'devices':devices,'master_count':len(masters),'registered_nodes':len(nodes),'online':sum(d['health']=='ONLINE' for d in devices),
      'local_ip':{key:listener.get(key) for key in ('state','listener_active','last_packet_error','last_database_persisted_at','accepted','rejected')},
      'mqtt':{key:mqtt.get(key) for key in ('state','last_error','subscription_state','acl_status','reconnect_count','tls_state','last_broker_puback_at')},
      'ethernet':'NOT_AVAILABLE','rf_observed_links':[],'rf_topology_state':'UNAVAILABLE_UNTIL_FIRMWARE_ROUTE_QUERY','parent_relationship_basis':'CONFIGURED_NOT_RF_VERIFIED'}

def install(app):
    @app.context_processor
    def navigation():return {'gateway_navigation':NAVIGATION}
    @app.get('/network')
    def network_page():return render_template('network.html')
    @app.get('/diagnostics')
    def diagnostics_page():return render_template('logs.html')
    @app.get('/api/operations/overview')
    def operations_overview():return jsonify(overview())
