// Execute the production renderer; check backend, picker and renderer parity.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'..'),context={window:{},gateway:{escape:s=>s}};
vm.runInNewContext(fs.readFileSync(path.join(root,'dashboard/static/js/sensor-widgets.js'),'utf8'),context);
const names=JSON.parse(fs.readFileSync(path.join(root,'backend/sensor_widgets.py'),'utf8').match(/ICONS = (\{[^\n]+\})/)[1].replace('{','[').replace('}',']'));
const picker=fs.readFileSync(path.join(root,'dashboard/static/js/sensor-management.js'),'utf8');
const render=context.window.SensorUI.icon,fallback=render({widget_config:{icon:'activity'}}),seen=new Set();
for(const name of names){assert.ok(picker.includes('"'+name+'"'),'picker: '+name);const svg=render({widget_config:{icon:name}});assert.ok(svg.startsWith('<svg'));assert.ok(svg.includes('aria-hidden="true"'));assert.ok(!seen.has(svg),'distinct icon: '+name);seen.add(svg);if(name!=='activity')assert.notEqual(svg,fallback,'no generic fallback: '+name);}
assert.equal(names.length,23);console.log('PASS: all 23 icons accepted, selectable and rendered distinctly (10 new + 13 existing).');
