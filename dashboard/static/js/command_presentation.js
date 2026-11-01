/* Human-readable projections of reported data and typed controls from the live registry. */
(function(scope){
 "use strict";
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const secret=k=>/password|secret|token|credential|^mesh_key$|^(mqtt_ca|gateway_ca|ca_cert)$|private_key/i.test(k);
 const names={seconds:'Interval (seconds)',expected_revision:'Configuration revision (from GET_CONFIG)',sleep_start_minute:'Sleep start time',sleep_duration_seconds:'Sleep duration (seconds)',duration_seconds:'Sleep duration (seconds)',sleep_mode:'ESP32 sleep mode',mode:'ESP32 sleep mode',lora_sleep_mode:'LoRa during ESP32 sleep',sleep_enabled:'Enable recurring sleep',sleep_days_mask:'Active days',utc_offset_minutes:'UTC offset (minutes)',wifi_rssi:'Wi-Fi signal',rssi:'Signal strength',station_ip:'Wi-Fi IP address',bus_voltage:'Bus voltage',shunt_voltage:'Shunt voltage',mq135_adc_raw:'MQ-135 ADC raw (uncalibrated)',mq135_pin_mv:'MQ-135 pin voltage',ok:'Device reported OK'};
 const hasPrivateFields=value=>Array.isArray(value)?value.some(hasPrivateFields):Boolean(value&&typeof value==='object'&&Object.entries(value).some(([k,v])=>secret(k)||hasPrivateFields(v)));
 const label=k=>names[k]||String(k).toLowerCase().replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
 function formatValue(key,value){
  if(value==null)return 'Not reported';if(typeof value==='boolean')return value?'Yes':'No';
  if(typeof value==='number'){
   if(key==='sleep_start_minute'&&value>=0&&value<1440)return String(Math.floor(value/60)).padStart(2,'0')+':'+String(value%60).padStart(2,'0');
   if(key==='sleep_days_mask')return ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].filter((_,i)=>value&(1<<i)).join(', ')||'No days';
   if(key==='utc_offset_minutes')return 'UTC'+(value<0?'-':'+')+String(Math.floor(Math.abs(value)/60)).padStart(2,'0')+':'+String(Math.abs(value)%60).padStart(2,'0');
   if(key==='seconds'||key.endsWith('_seconds')||['uptime_s','keepalive_s'].includes(key)){const h=Math.floor(value/3600),m=Math.floor(value%3600/60),sec=value%60;return value>=60?[h?h+' h':'',m?m+' min':'',sec?sec+' s':''].filter(Boolean).join(' ')+' ('+value+' s)':value+' s';}
   const units={temperature:'°C',humidity:'%RH',bus_voltage:'V',shunt_voltage:'mV',current:'A',power:'W',mq135_pin_mv:'mV',mq135_adc_raw:'counts',rssi:'dBm',wifi_rssi:'dBm'};
   if(units[key])return value+' '+units[key];
  }
  return String(value);
 }
 function readable(value,depth=0){
  if(depth>4)return '<p class="command-result-note">More detail is available in JSON.</p>';
  if(Array.isArray(value))return value.length?value.slice(0,16).map((v,i)=>'<section class="command-result-group"><h5>Item '+(i+1)+'</h5>'+readable(v,depth+1)+'</section>').join(''):'<p class="command-result-note">No items reported.</p>';
  if(value&&typeof value==='object'){
   const items=Object.entries(value).filter(([k])=>!secret(k)).slice(0,48);let fields='',groups='';
   for(const [key,val] of items){
    if(val&&typeof val==='object')groups+='<section class="command-result-group"><h5>'+esc(label(key))+'</h5>'+readable(val,depth+1)+'</section>';
    else {let text=formatValue(key,val);if(text.length>600)text=text.slice(0,600)+'…';fields+='<div><dt>'+esc(label(key))+'</dt><dd>'+esc(text)+'</dd></div>';}
   }
   if(Number.isInteger(value.sleep_start_minute)&&Number.isInteger(value.sleep_duration_seconds)){
    const total=value.sleep_start_minute*60+value.sleep_duration_seconds,sec=total%86400;
    const wake=[Math.floor(sec/3600),Math.floor(sec/60)%60,sec%60].map(v=>String(v).padStart(2,'0')).join(':');
    fields+='<div><dt>Scheduled wake time (calculated)</dt><dd>'+wake+(total>=86400?' · next day':'')+'</dd></div>';
   }
   return (fields?'<dl class="command-readable-values">'+fields+'</dl>':'')+groups||'<p class="command-result-note">No non-secret fields reported.</p>';
  }
  return '<p class="command-result-note">'+esc(value==null?'No payload reported.':value)+'</p>';
 }
 const enums={role:['MASTER','NODE'],routing:['MASTER_ONLY','DIRECT_ONLY','DIRECT_PREFERRED'],sleep_mode:['DEEP','LIGHT'],lora_sleep_mode:['KEEP','DEEP'],radio_mode:['NORMAL','WOR_TX','WOR_RX']};
 class Forms {
  constructor(container,revision){this.container=container;this.revision=revision;this.ready=false;this.registry={};this.fields={};this.type='';}
  catalog(data){this.registry={...data.command_registry,...data.operational_registry};this.fields=data.fields||{};this.ready=true;}
  add(key,spec={},value=''){
   const wrapper=document.createElement('label');wrapper.className='command-field';const title=document.createElement('span');title.textContent=label(key);wrapper.append(title);
   let input;const options=spec.values||enums[spec.type];
   if(options){input=document.createElement('select');for(const val of options){const option=document.createElement('option');option.value=val;option.textContent=val;input.append(option);}}
   else{input=document.createElement('input');input.type=['int','integer'].includes(spec.type)?'number':['bool','boolean'].includes(spec.type)?'checkbox':spec.type==='time'?'time':'text';}
   input.id='command-field-'+key;input.dataset.argument=key;input.dataset.kind=spec.type||'text';input.required=Boolean(spec.required)&&input.type!=='checkbox';
   if(input.type==='number'){input.step='1';if(spec.minimum!=null)input.min=spec.minimum;if(spec.maximum!=null)input.max=spec.maximum;}
   if(input.type==='checkbox')input.checked=value===true;else input.value=String(value);
   const max=spec.maximum_utf8_bytes||(['text','id'].includes(spec.type)?spec.maximum:null);if(max)input.dataset.maxBytes=max;
   wrapper.append(input);this.container.append(wrapper);return input;
  }
  note(text){const p=document.createElement('p');p.className='command-form-note';p.textContent=text;this.container.append(p);return p;}
  render(type){
   this.type=type;this.container.replaceChildren();const definition=this.registry[type];
   if(!definition){this.note(this.ready?'Command is not in the supported registry.':'Loading supported command controls…');return;}
   if(type==='PING'){this.note('Enter the echo message next to Send. A device RESPONSE is required to confirm the round trip.');return;}
   if(type==='SET_SLEEP_SCHEDULE'){
    this.add('sleep_enabled',{type:'bool'},false);this.add('sleep_mode',{type:'sleep_mode'},'DEEP');this.add('lora_sleep_mode',{type:'lora_sleep_mode'},'KEEP');
    const start=this.add('sleep_start_minute',{type:'time',required:true},'23:00');const wake=this.add('wake_time',{type:'time',required:true},'07:00');wake.previousElementSibling.textContent='Wake-up time (calculated request)';
    const duration=this.add('sleep_duration_seconds',{type:'int',minimum:60,maximum:86400,required:true},28800);
    const secs=value=>{const [h,m,s=0]=value.split(':').map(Number);return h*3600+m*60+s;};const clock=n=>[Math.floor(n/3600),Math.floor(n/60)%60,n%60].map(v=>String(v).padStart(2,'0')).join(':');wake.step='1';
    const fromTimes=()=>{if(start.value&&wake.value)duration.value=(secs(wake.value)-secs(start.value)+86400)%86400||86400;};
    start.oninput=wake.oninput=fromTimes;duration.oninput=()=>{if(start.value&&Number.isInteger(Number(duration.value)))wake.value=clock((secs(start.value)+Number(duration.value))%86400);};
    const days=document.createElement('fieldset');days.className='command-days';const legend=document.createElement('legend');legend.textContent='Active days';days.append(legend);
    ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].forEach((day,index)=>{const l=document.createElement('label'),c=document.createElement('input');c.type='checkbox';c.checked=true;c.dataset.day=String(index);l.append(c,document.createTextNode(day));days.append(l);});this.container.append(days);
    this.add('utc_offset_minutes',{type:'int',minimum:-720,maximum:840,required:true},-new Date().getTimezoneOffset());this.add('expected_revision',{type:'int',minimum:0,maximum:4294967294,required:true},this.revision()??'');
    this.note('Wake time and duration describe the requested schedule, not confirmed sleep or wake-up. Same start/wake time means 24 hours. Overnight schedules are supported. Fetch GET_CONFIG for the current revision.');return;
   }
   if(type==='CONFIG_UPDATE'){
    const keys=Object.keys(this.fields).filter(k=>k!=='local_ip_enabled').sort();const chooser=this.add('config_field',{type:'enum',values:keys},keys[0]);chooser.previousElementSibling.textContent='Setting to change';
    const renderValue=()=>{this.container.querySelectorAll('[data-config-value]').forEach(e=>e.remove());const k=chooser.value;const val=this.add(k,{...this.fields[k],required:true},'');val.parentElement.dataset.configValue='1';
     if(k==='wifi_dhcp'){val.checked=true;val.onchange=()=>{this.container.querySelectorAll('[data-static-network]').forEach(e=>e.remove());if(!val.checked)for(const field of ['wifi_ip','wifi_subnet','wifi_gateway','wifi_dns','wifi_dns2']){const input=this.add(field,{...this.fields[field],required:field!=='wifi_dns2'},'');input.parentElement.dataset.staticNetwork='1';input.parentElement.dataset.configValue='1';}};}
    };chooser.onchange=renderValue;renderValue();this.add('expected_revision',{type:'int',minimum:0,maximum:4294967294,required:true},this.revision()??'');this.note('Only the selected setting is sent. Use Master / Node controls for password-confirmed IP/MQTT transport switching. Radio changes require verified hardware and regional settings.');return;
   }
   const args=definition.arguments||{};
   for(const [key,descriptor] of Object.entries(args)){
    let spec={...descriptor},value='';
    if(key==='seconds')value=type==='SET_HEARTBEAT_INTERVAL'?30:10;
    if(key==='duration_seconds')value=60;
    if(key==='mode')value='DEEP';
    if(key==='restore_after_seconds')value=15;
    if(key==='timeout_seconds')value=10;
    if(key==='unix_time')value=Math.floor(Date.now()/1000);
    if(key==='scope')value='NETWORK';
    if(key==='expected_revision')value=this.revision()??'';
    if(key==='device_name')spec.required=true;
    this.add(key,spec,value);
   }
   if(['SET_TELEMETRY_INTERVAL','SET_HEARTBEAT_INTERVAL'].includes(type))this.note('Interval in seconds. Examples: 2, 5, 10, 30 or 60; custom values must stay within the shown limits.');
   if(type==='SLEEP_NOW')this.note('Sleep duration begins after the device completes preparation and enters sleep. Commands may be unavailable while asleep. The response must confirm execution.');
   if(!Object.keys(args).length)this.note('This command has no arguments. Delivery policy is available below.');
  }
  payload(){
   if(!this.ready||!this.registry[this.type])throw Error('Supported command registry is unavailable.');
   const output={};for(const input of this.container.querySelectorAll('[data-argument]')){
    const key=input.dataset.argument;if(key==='config_field')continue;
    if(input.type!=='checkbox'&&input.value===''){if(input.required)throw Error(label(key)+' is required.');continue;}
    if(!input.checkValidity())throw Error('Check '+label(key)+' and its allowed range.');
    if(key==='wake_time')continue;
    let value=input.type==='checkbox'?input.checked:input.type==='number'?Number(input.value):input.value;
    if(input.type==='number'&&!Number.isInteger(value))throw Error(label(key)+' must be a whole number.');
    if(input.dataset.maxBytes&&new TextEncoder().encode(String(value)).length>Number(input.dataset.maxBytes))throw Error(label(key)+' is too long.');
    if(key==='confirm'&&value!==true)throw Error('Confirm this operation before sending.');
    if(key==='sleep_start_minute'){const [h,m]=value.split(':').map(Number);value=h*60+m;}
    output[key]=value;
   }
   if(this.type==='SET_SLEEP_SCHEDULE'){output.sleep_days_mask=[...this.container.querySelectorAll('[data-day]:checked')].reduce((mask,c)=>mask|(1<<Number(c.dataset.day)),0);if(!output.sleep_days_mask)throw Error('Select at least one active day.');}
   return output;
  }
 }
 const api={readable,label,Forms,hasPrivateFields,formatValue};if(typeof module!=='undefined'&&module.exports)module.exports=api;else scope.CommandPresentation=api;
})(typeof window==='undefined'?globalThis:window);
