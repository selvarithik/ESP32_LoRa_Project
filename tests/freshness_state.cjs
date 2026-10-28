const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const now=Date.parse('2026-10-25T12:00:00Z');
class ClockDate extends Date{static now(){return now;}}
const context={window:{},gateway:{escape:String},Date:ClockDate};vm.runInNewContext(fs.readFileSync('dashboard/static/js/sensor-widgets.js','utf8'),context);
const ui=context.window.SensorUI,saved=Object.freeze({stale_timeout:10}),p={timestamp:new Date(now-12000).toISOString(),widget_config:saved,data_type:'FLOAT',value:25,quality:'GOOD'};
assert.equal(ui.status(p),'Stale');assert.equal(ui.status({...p,effective_stale_timeout_s:25}),'Live');
assert.equal(ui.status({...p,effective_stale_timeout_s:25,timestamp:new Date(now-26000).toISOString()}),'Stale');
assert.equal(ui.status({...p,effective_stale_timeout_s:25,timestamp:null}),'Unavailable');
assert.equal(ui.status({...p,effective_stale_timeout_s:25},{enabled:false}),'Offline');
assert.equal(ui.status({...p,effective_stale_timeout_s:25,quality:'BAD'}),'BAD');
assert.equal(ui.freshnessTimeout({...p,effective_stale_timeout_s:25,widget_config:{stale_timeout:120}}),120);
assert.equal(saved.stale_timeout,10);
console.log('PASS shared sensor freshness: cadence grace, missing samples, actual expiry, offline/quality states and preserved saved timeout');
