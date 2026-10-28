// Execute production execution-outcome projection; ACK never invents execution.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(require('node:path').join(__dirname,'../dashboard/static/js/command_center.js'),'utf8');
const outcome=vm.runInNewContext('('+source.match(/function outcome\(cmd\)\{[^}]+\}/)[0]+')',{terminal:new Set(['COMPLETED','FAILED','TIMEOUT','CANCELLED'])});
for(const state of ['QUEUED','SENT','ACK_RECEIVED','EXECUTING'])assert.equal(outcome({state}),'Pending');
for(const state of ['FAILED','TIMEOUT','CANCELLED','COMPLETED'])assert.equal(outcome({state}),'Not reported');
assert.equal(outcome({state:'COMPLETED',response_at:'2026-10-27T17:00:00Z'}),'COMPLETED');
assert.equal(outcome({state:'FAILED',response_at:'2026-10-27T17:00:00Z'}),'FAILED');
console.log('PASS production outcome projection: queue, ACK, missing response, timeout, confirmed completion/failure');
