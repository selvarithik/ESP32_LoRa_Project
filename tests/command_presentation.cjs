const assert=require('node:assert/strict');
const {readable,hasPrivateFields,formatValue}=require('../dashboard/static/js/command_presentation.js');
const html=readable({ok:false,count:0,station_ip:'192.168.1.106',nested:{mesh_key:'private-sentinel',password:'private-sentinel',items:[{token:'private-sentinel',message:'<img src=x onerror=alert(1)>'}]}});
assert(!html.includes('private-sentinel'));assert(!html.includes('<img'));assert(html.includes('&lt;img'));assert(html.includes('192.168.1.106'));assert(html.includes('>No<'));assert(html.includes('>0<'));
let nested='deep';for(let i=0;i<8;i++)nested={child:nested};assert(readable(nested).includes('More detail'));
console.log('PASS production readable renderer: nested secret exclusion, HTML escaping, explicit false/zero and bounded nesting');

assert(hasPrivateFields({nested:[{wifi_password:'private-sentinel'}]}));assert(!hasPrivateFields({seconds:10,expected_revision:3}));

assert.equal(formatValue('sleep_start_minute',1380),'23:00');assert.equal(formatValue('utc_offset_minutes',330),'UTC+05:30');assert.equal(formatValue('sleep_days_mask',3),'Sun, Mon');assert.equal(formatValue('seconds',10),'10 s');assert.match(formatValue('sleep_duration_seconds',28800),/8 h/);

assert.match(readable({sleep_start_minute:1380,sleep_duration_seconds:28800}),/07:00:00.*next day/);
