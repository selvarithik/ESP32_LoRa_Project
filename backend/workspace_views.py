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
 {'label':'System','children':[{'label':'Health','path':'/system-overview'},{'label':'Master / Node Controls','path':'/device-controls'},{'label':'Local IP Communication','path':'/local-ip'},{'label':'Logs','path':'/logs'}]},
 {'label':'Settings','path':'/system'},{'label':'Existing tools','children':[{'label':'Firmware','path':'/firmware'},{'label':'Private Chat','path':'/chat'}]}]

def public_radio_signal(value):
    value = value if isinstance(value, dict) else {}
    raw = value.get('rssi_raw')
    raw = raw if type(raw) is int and 0 <= raw <= 255 else None
    dbm = raw - 256 if raw is not None else value.get('rssi_dbm')
    valid = type(dbm) is int and -141 <= dbm <= -11 and value.get('rssi_valid') is not False
    result = {'rssi_raw': raw, 'rssi_valid': valid, 'rssi_dbm': dbm if valid else None}
    for name in ('age_ms', 'valid_age_ms', 'valid_count', 'min_dbm', 'max_dbm', 'avg_dbm'):
        if type(value.get(name)) in (int, float):
            result[name] = value[name]
    return result

RADIO_CONFIG_FIELDS = {
    'address': int, 'baud': int, 'uart_parity': str, 'channel': int,
    'air_rate_code': int, 'air_rate_bps': int, 'power_dbm': int,
    'subpacket_bytes': int, 'wor_cycle_ms': int, 'fixed_mode': bool,
    'rssi_enabled': bool, 'noise_rssi_enabled': bool, 'lbt': bool,
}

def radio_config_view(value):
    if not isinstance(value, dict):
        return None
    config = {k: value[k] for k, kind in RADIO_CONFIG_FIELDS.items() if type(value.get(k)) is kind}
    channel, power = config.get('channel'), config.get('power_dbm')
    if channel is None or not 0 <= channel <= 80 or power not in (10, 13, 17, 22):
        return None
    frequency = 850125 + 1000 * channel
    config.update(frequency_khz=frequency, key='not readable',
                  frequency_flag='OK' if 865000 <= frequency - 62.5 and frequency + 62.5 <= 868000 else 'RED',
                  power_flag='RED' if power > 13 else 'AMBER' if power > 10 else 'OK')
    return config

RADIO_METRIC_FIELDS = ('tx_fragments', 'rx_fragments', 'delivered', 'rejects',
                       'auth_failures', 'protocol_mismatches', 'timeouts',
                       'budget_refusals', 'used_us', 'limit_us', 'remaining_us',
                       'last_fragment_us', 'poll_interval_ms', 'next_tx_gap_ms')

def radio_metrics_view(value, signal, elapsed_ms=None):
    if not isinstance(value, dict):
        return None
    result = {key: value[key] for key in RADIO_METRIC_FIELDS
              if type(value.get(key)) is int and value[key] >= 0}
    used, limit = result.get('used_us'), result.get('limit_us')
    valid_age = signal.get('valid_age_ms')
    alarms = []
    if elapsed_ms is not None and (valid_age or 0) + elapsed_ms >= 600000:
        alarms.append('NO_RECENT_VALID_RSSI')
    if result.get('auth_failures', 0) >= 3:
        alarms.append('AUTH_FAILURES')
    if result.get('protocol_mismatches', 0):
        alarms.append('PROTOCOL_MISMATCH')
    if used is not None and limit and used * 5 > limit * 4:
        alarms.append('AIRTIME_OVER_80_PERCENT')
    if elapsed_ms is not None and result.get('poll_interval_ms') and elapsed_ms >= result['poll_interval_ms'] * 3:
        alarms.append('STALE_RADIO_REPORT')
    result.update(model_verified=False, alarms=alarms)
    return result

def report_age_ms(stamp):
    try:
        report_time = datetime.fromisoformat(stamp)
        return max(0, int((datetime.now(report_time.tzinfo)-report_time).total_seconds()*1000))
    except (ValueError, TypeError):
        return None

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
            device['radio_signal']=public_radio_signal(reported.get('radio_signal'))
            device['radio_config']=radio_config_view(reported.get('radio_config'))
            device['radio_metrics']=radio_metrics_view(reported.get('radio_metrics'), device['radio_signal'],
                                                        report_age_ms(reported.get('radio_report_received_at')))
            device['last_commands']=[dict(cmd) for cmd in db.execute(
                'SELECT command_id, command_type, state, created_at FROM commands WHERE node_id=? ORDER BY created_at DESC LIMIT 4',
                (row['node_id'],))]
            ina=db.execute("""SELECT parameter_id,timestamp,value FROM telemetry_values WHERE node_id=?
                AND parameter_id IN ('bus_voltage','shunt_voltage','current','power')
                AND timestamp=(SELECT max(timestamp) FROM telemetry_values WHERE node_id=? AND parameter_id='bus_voltage')""",
                (row['node_id'],row['node_id'])).fetchall()
            device['ina219']={'timestamp':ina[0]['timestamp'],
                              'values':{field['parameter_id']:field['value'] for field in ina}} if ina else None
            device['diagnostics']={}
            for kind in ('GET_NETWORK','GET_RADIO_STATUS','GET_MESH_STATUS','GET_ROUTE_INFO'):
                command=db.execute("SELECT result,response_at FROM commands WHERE node_id=? AND command_type=? AND state='COMPLETED' ORDER BY response_at DESC LIMIT 1",(row['node_id'],kind)).fetchone()
                if not command:continue
                try:value=json.loads(command['result'] or '{}')
                except (ValueError,TypeError):continue
                allowed={'GET_NETWORK':('connected','station_ip','ip','rssi','dhcp','subnet','gateway','dns','disconnect_reason','reconnect_attempts'),'GET_RADIO_STATUS':('state','error','public_settings_read','register_writes','rx_messages','tx_uart_fragments','rejected','auth_failures','timeouts','observed','hardware_link_verified','rf_receive_state','last_rf_peer','last_rf_age_ms','rssi_dbm','rssi_raw','rssi_valid'),'GET_MESH_STATUS':('radio_state','hardware_verified','node_count','route_count','pending','delivery_failures','duplicates'),'GET_ROUTE_INFO':('radio_state','hardware_verified','routes')}[kind]
                if isinstance(value,dict):
                    projected={key:value.get(key) for key in allowed if key in value and (key in ('observed','routes') or type(value.get(key)) in (str,int,float,bool,type(None)))}
                    if kind=='GET_RADIO_STATUS':
                        projected.update(public_radio_signal(projected))
                    if 'observed' in projected:
                        observed=projected['observed'];projected['observed']={key:observed[key] for key in ('address','baud','channel','air_rate_code','power_dbm','subpacket_bytes','fixed_mode','rssi_enabled','lbt') if isinstance(observed,dict) and key in observed and type(observed[key]) in (str,int,float,bool,type(None))}
                    if 'routes' in projected:
                        projected['routes']=[{key:route[key] for key in ('destination','next_hop','hop_count','age_ms') if key in route and type(route[key]) in (str,int,float,bool,type(None))} for route in projected['routes'][:12] if isinstance(route,dict)] if isinstance(projected['routes'],list) else []
                    device['diagnostics'][kind]={'received_at':command['response_at'],'data':projected}
            devices.append(device)
    finally:db.close()
    masters=[d for d in devices if d['device_role']=='MASTER'];nodes=[d for d in devices if d['device_role']=='NODE']
    for device in devices:
        peer = next((m for m in masters if m['node_id']==device['master_id']), None)
        config = device['radio_config']
        if peer and peer is not device and config and peer['radio_config']:
            master = peer['radio_config']
            config['peer_match'] = all(key in config and key in master and config[key]==master[key]
                                       for key in ('channel','air_rate_code','address'))
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
