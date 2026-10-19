const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
(async()=>{const b=await chromium.launch({channel:'msedge',headless:true});try{
 const c=await b.newContext(),base='http://127.0.0.1:5080';
 const r=await c.request.get(base+'/login'),csrf=(await r.text()).match(/data-csrf="([^"]+)"/)[1];
 assert((await c.request.post(base+'/api/auth/login',{headers:{'X-CSRF-Token':csrf},data:{username:'admin',password:'fixture-only-admin-123'}})).ok());
 const p=await c.newPage();await p.goto(base+'/');
 await p.waitForFunction(()=>document.getElementById('dashboard-node-list').textContent.includes('Bus Voltage'));
 const t=await p.locator('#dashboard-node-list').textContent();assert(t.includes('Mq135 Adc Raw'));assert(t.includes('SIMULATED'));assert(t.includes('Current'));assert(t.includes('Power'));
 const snapshot=await (await c.request.get(base+'/api/live/snapshot')).json();assert(JSON.stringify(snapshot).includes('current'));assert(JSON.stringify(snapshot).includes('power'));
 for(const width of [375,1440]){await p.setViewportSize({width,height:960});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
 console.log('PASS actual temporary Gateway dashboard renders SIMULATED INA219/MQ135/DHT samples; mobile and desktop have no overflow. No hardware claim.');
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
