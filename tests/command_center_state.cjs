// Executes the real production online predicate; no device or database changes.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(require('node:path').join(__dirname,'../dashboard/static/js/command_center.js'),'utf8');
class Clock extends Date{static now(){return Date.parse('2026-10-25T06:00:00Z');}}
const online=vm.runInNewContext(source.match(/const online=([^;]+);/)[1],{Date:Clock});
const node={status:'online',enabled:1,device_enrolled:1,heartbeat_seconds:120,last_seen:'2026-10-25T05:58:45Z'};
assert.equal(Boolean(online(node)),true,'75s age remains online with120s heartbeat');
assert.equal(Boolean(online({...node,last_seen:'2026-10-25T05:53:59Z'})),false,'Older than3 heartbeats');
assert.equal(Boolean(online({...node,device_enrolled:0})),false,'Legacy60s timeout retained');
assert.equal(Boolean(online({...node,enabled:0})),false,'Numeric disabled flag');
assert.equal(Boolean(online({...node,enabled:false})),false,'Boolean disabled flag');
assert.equal(Boolean(online({...node,last_seen:'invalid'})),false,'Invalid timestamp fails closed');
assert.equal(Boolean(online({...node,status:'offline'})),false,'Backend offline state retained');
console.log('PASS Command Center production heartbeat/disable/freshness predicate');
