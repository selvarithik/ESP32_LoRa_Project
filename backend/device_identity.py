"""Reversible aliases: immutable legacy routing IDs stay unchanged in storage."""
import re
MAC=re.compile(r'^[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}$')
LEGACY=re.compile(r'^ESP32-([0-9A-Fa-f]{12})$',re.IGNORECASE)
def hardware_mac(identity):
 if not isinstance(identity,str):raise ValueError('INVALID_DEVICE_ID')
 if MAC.fullmatch(identity):return identity.upper()
 match=LEGACY.fullmatch(identity)
 if match:
  parts=[match[1][i:i+2] for i in range(0,12,2)]
  return ':'.join(reversed(parts)).upper()
 raise ValueError('INVALID_MAC_DEVICE_ID')
def resolve(identity,db):
 if not isinstance(identity,str):raise ValueError('INVALID_DEVICE_ID')
 if db.execute('SELECT 1 FROM nodes WHERE node_id=?',(identity,)).fetchone():return identity
 mac=hardware_mac(identity)
 for row in db.execute('SELECT node_id FROM nodes WHERE device_enrolled=1'):
  try:
   if hardware_mac(row['node_id'])==mac:return row['node_id']
  except ValueError:continue
 raise ValueError('DEVICE_NOT_ENROLLED')


def require_available_hardware(identity,db):
 """Reject MAC aliases without renaming legacy routing IDs or device labels."""
 import json
 try:candidate=hardware_mac(identity)
 except ValueError:return
 for row in db.execute('SELECT * FROM nodes WHERE node_id!=?',(identity,)):
  entry=dict(row)
  try:known=hardware_mac(entry['node_id'])
  except ValueError:
   try:known=hardware_mac(json.loads(entry.get('latest_status') or '{}').get('hardware_mac',''))
   except (ValueError,TypeError,AttributeError):known=None
  if known==candidate:raise ValueError('Hardware MAC already enrolled; use the existing device identity')
