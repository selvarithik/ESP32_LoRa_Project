"""Retained monitoring projection from authenticated Gateway observations."""
from datetime import datetime
import json

from workspace_views import radio_config_view, public_radio_signal, radio_metrics_view

def prefix(profile):
    return f"{profile['topic_prefix']}/{profile['gateway_id']}/lora"

def will(profile):
    return f"{prefix(profile)}/availability", {
        'schema_version': 1, 'online': False, 'source': 'gateway'
    }

def retained_topics(profile, node, now, ina219=None, command=None):
    try:
        status = json.loads(node['latest_status'] or '{}')
    except (ValueError, TypeError):
        status = {}
    if not isinstance(status, dict):
        status = {}
    signal = public_radio_signal(status.get('radio_signal'))
    config = radio_config_view(status.get('radio_config'))
    try:
        age = max(0, int((now - datetime.fromisoformat(node['last_seen'])).total_seconds()*1000))
    except (ValueError, TypeError):
        age = None
    metrics = radio_metrics_view(status.get('radio_metrics'), signal, age) or {}
    period = metrics.get('poll_interval_ms') or status.get('radio_poll_interval_ms') or 60000
    online = age is not None and type(period) is int and period > 0 and age < 3 * period
    ident = node['node_id']
    base = f"{prefix(profile)}/{ident}"
    common = {'schema_version': 1, 'node_id': ident, 'observed_at': node['last_seen']}
    # Score a link only when a recent, valid packet RSSI and delivery counters exist.
    level = None
    if signal['rssi_valid'] and online:
        strength = 4 if signal['rssi_dbm'] >= -70 else 3 if signal['rssi_dbm'] >= -90 else 2 if signal['rssi_dbm'] >= -110 else 1
        received, rejects = metrics.get('rx_fragments', 0), metrics.get('rejects', 0)
        level = min(strength, 2) if received and received / (received + rejects) < .8 else strength
    return {f"{base}/{name}": {**common, **body} for name, body in {
        'status': {'role': node['device_role'], 'firmware_version': node['firmware_version'],
                   'build': 'bench' if status.get('bench_build') is True else 'production' if status.get('bench_build') is False else None,
                   'online': online, 'last_seen_age_ms': age, 'last_command': command},
        'link': {**signal, 'level': level},
        'config': {'radio': config, 'basis': 'advisory, not a legal approval'},
        'airtime': {**{key: metrics.get(key) for key in ('used_us', 'limit_us', 'remaining_us', 'last_fragment_us', 'poll_interval_ms', 'next_tx_gap_ms')}, 'model': 'modeled, unverified'},
        'counters': {key: metrics.get(key) for key in ('tx_fragments', 'rx_fragments', 'delivered', 'retries', 'rejects', 'auth_failures', 'protocol_mismatches', 'budget_refusals', 'queue_drops')},
        'alarms': {'active': sorted(set(metrics.get('alarms', ())) | (set() if online else {'NODE_OFFLINE'}))},
        'telemetry/ina219': {'reading': ina219},
    }.items()}
