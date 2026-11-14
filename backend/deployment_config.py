"""Non-secret local deployment options. No broker/device settings belong here."""
import ipaddress,json
from pathlib import Path
from urllib.parse import urlsplit
DEFAULTS=dict(mode='local',host='127.0.0.1',port=5000,threads=16,allowed_hosts=['127.0.0.1','localhost'],trusted_proxies=[],public_url='',backup_hours=24,backup_keep=7)
class DeploymentError(ValueError):pass

def load(path=None):
 d=dict(DEFAULTS)
 if path:
  try:
   raw=json.loads(Path(path).read_text(encoding='utf-8'))
   if not isinstance(raw,dict) or set(raw)-set(d):raise ValueError()
   d.update(raw)
  except (OSError,ValueError,TypeError):raise DeploymentError('INVALID_DEPLOYMENT_CONFIG') from None
 return validate(d)

def validate(d):
 try:
  if d['mode'] not in ('local','proxy') or not ipaddress.ip_address(d['host']).is_loopback:raise ValueError()
  for key,lo,hi in [('port',1024,65535),('threads',8,64),('backup_hours',1,168),('backup_keep',2,60)]:
   if type(d[key]) is not int or not lo<=d[key]<=hi:raise ValueError()
  if not isinstance(d['allowed_hosts'],list) or not d['allowed_hosts'] or any(not isinstance(x,str) or not x or any(c in x for c in '/:* \r\n') for x in d['allowed_hosts']):raise ValueError()
  if not isinstance(d['trusted_proxies'],list):raise ValueError()
  for p in d['trusted_proxies']:ipaddress.ip_network(p,strict=False)
  u=urlsplit(d['public_url'])
  if d['mode']=='proxy' and (not d['trusted_proxies'] or u.scheme!='https' or u.hostname not in d['allowed_hosts'] or u.username or u.password or u.query or u.fragment):raise ValueError()
  if d['mode']=='local' and (d['trusted_proxies'] or d['public_url']):raise ValueError()
 except (ValueError,TypeError,KeyError):raise DeploymentError('UNSAFE_DEPLOYMENT_CONFIG') from None
 return d


def load_portable(path):
 path=Path(path)
 if not path.is_file():
  raise DeploymentError('Missing config.json beside the executable. Copy config.example.json to config.json and fill in the settings.')
 try:
  raw=json.loads(path.read_text(encoding='utf-8-sig'))
  if not isinstance(raw,dict) or set(raw)-{'server','admin_pin','mqtt','mqtt_acl_confirmed'}:raise ValueError()
  if type(raw.get('mqtt_acl_confirmed',False)) is not bool:raise ValueError()
  server=raw.get('server',{})
  if not isinstance(server,dict) or set(server)-set(DEFAULTS):raise ValueError()
 except (OSError,ValueError,TypeError):
  raise DeploymentError('Invalid config.json. Compare it with config.example.json.') from None
 settings=validate({**DEFAULTS,**server})
 if settings['mode']!='local':raise DeploymentError('The packaged Gateway requires local mode.')
 return settings,raw
