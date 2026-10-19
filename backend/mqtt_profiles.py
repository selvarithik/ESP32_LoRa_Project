"""Named non-secret profile templates. Selection only stages the existing transaction."""
import json
from flask import jsonify,request
import mqtt_api,mqtt_contract as contract,device_api
class Catalog:
 def __init__(self,store):
  self.store=store
  with store.connect() as db:db.execute("CREATE TABLE IF NOT EXISTS mqtt_profile_catalog (id INTEGER PRIMARY KEY CHECK(id=1),revision INTEGER NOT NULL,document TEXT NOT NULL)");db.execute("INSERT OR IGNORE INTO mqtt_profile_catalog VALUES(1,0,'{}')")
 def read(self):
  with self.store.connect() as db:row=db.execute('SELECT revision,document FROM mqtt_profile_catalog WHERE id=1').fetchone()
  return dict(schema_version=1,catalog_revision=row['revision'],profiles=[{k:v for k,v in p.items() if k in contract.FIELDS and k!='password'} for p in json.loads(row['document']).values()])
 def change(self,operation,data):
  contract.require(operation in ('save','delete'))
  with self.store.connect() as db:
   db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT revision,document FROM mqtt_profile_catalog WHERE id=1').fetchone();revision=row['revision'];profiles=json.loads(row['document'])
   contract.require(contract.integer(data.get('catalog_revision')) and data['catalog_revision']==revision,code='REVISION_CONFLICT')
   if operation=='save':
    contract.require(set(data)=={'catalog_revision','profile'});profile=dict(data['profile']);contract.require(contract.preserved(profile.get('password')),code='PROTECTED_PROVISIONING_REQUIRED');profile['password']='';contract.validate_profile(profile);profile.pop('password');name=profile['profile_name'];contract.require(name in profiles or len(profiles)<4,code='CATALOG_FULL');profiles[name]=profile
   else:
    contract.require(set(data)=={'catalog_revision','profile_name','confirm_profile_name'});name=data['profile_name'];contract.require(name==data['confirm_profile_name'],code='CONFIRMATION_REQUIRED');contract.require(name in profiles,code='PROFILE_NOT_FOUND');contract.require(name!=(self.store.read().get('active') or {}).get('profile_name'),code='ACTIVE_PROFILE_PROTECTED');del profiles[name]
   db.execute('UPDATE mqtt_profile_catalog SET revision=?,document=? WHERE id=1',(revision+1,contract.canonical(profiles)))
  return self.read()
 def select(self,data):
  contract.require(set(data)=={'catalog_revision','expected_revision','profile_name'})
  value=self.read();contract.require(contract.integer(data['catalog_revision']) and value['catalog_revision']==data['catalog_revision'],code='REVISION_CONFLICT');profile=next((p for p in value['profiles'] if p['profile_name']==data['profile_name']),None);contract.require(profile is not None,code='PROFILE_NOT_FOUND');return self.store.stage(profile,data['expected_revision'])
def install(app):
 @app.get('/api/mqtt/profiles')
 @device_api.require_admin
 def profiles_get():return jsonify(Catalog(mqtt_api.service().store).read())
 @app.post('/api/mqtt/profiles/<operation>')
 @device_api.require_admin
 def profiles_action(operation):
  try:
   contract.require(request.is_json and (request.content_length or 0)<=8192);data=contract.loads(request.get_data(),8192);catalog=Catalog(mqtt_api.service().store);return jsonify(catalog.select(data) if operation=='select' else catalog.change(operation,data))
  except contract.ContractError as error:return jsonify(error=dict(code=error.code,field=error.field)),409
  except (ValueError,TypeError,KeyError):return jsonify(error=dict(code='INVALID_REQUEST')),400

 @app.post('/api/mqtt/runtime/<operation>')
 @device_api.require_admin
 def runtime_action(operation):
  try:
   contract.require(operation in ('connect','disconnect'))
   contract.require(request.is_json and (request.content_length or 0)<=256);data=contract.loads(request.get_data(),256);contract.require(set(data)=={'expected_revision'})
   current=mqtt_api.service();state=current.store.read();contract.require(contract.integer(data['expected_revision']) and state['revision']==data['expected_revision'],code='REVISION_CONFLICT')
   contract.require(state['transaction']['state'] in ('IDLE','PENDING','ROLLED_BACK','COMMITTED','FAILED'),code='TRANSACTION_BUSY')
   if operation=='connect':
    contract.require(current.trust_acl,code='ACL_CONFIRMATION_REQUIRED');contract.require(state.get('active') is not None,code='ACTIVE_PROFILE_REQUIRED');current.start()
   else:current.stop()
   return jsonify(requested=True,runtime=current.status()),202
  except contract.ContractError as error:return jsonify(error=dict(code=error.code)),409
  except Exception:return jsonify(error=dict(code='RUNTIME_OPERATION_FAILED')),503
