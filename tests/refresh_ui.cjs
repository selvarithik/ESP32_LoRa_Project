/* Actual disposable Flask, SQLite, Socket.IO and signed local TCP exchanges. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const base='http://127.0.0.1:5062',device='REFRESH-MASTER';
const key=crypto.createHash('sha256').update('fixture-refresh-token-only-not-deployment').digest();
let sequence=0;const runId=crypto.randomBytes(4).toString("hex");
function crc32(raw){let c=0xffffffff;for(const b of raw){c^=b;for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0);}return (c^0xffffffff)>>>0;}
async function publish(value){
 const challenge=await (await fetch('http://127.0.0.1:5063/api/v1/device/local-challenge',{headers:{'X-Device-ID':device}})).json();
 const payload=JSON.stringify({valid:true,parameters:{temperature:value,humidity:61}}),raw=Buffer.from(payload);
 const frame={protocol_version:1,message_id:'REFRESH-'+runId+'-'+(++sequence),source:device,destination:'GATEWAY',origin_id:device,final_destination_id:'GATEWAY',next_hop:'GATEWAY',type:'TELEMETRY',ttl:5,timestamp:Math.floor(Date.now()/1000),sequence_number:sequence,correlation_id:'',payload,payload_length:raw.length,payload_crc32:crc32(raw)};
 const body=JSON.stringify(frame),proof=crypto.createHmac('sha256',key).update('LOCALIP1\n'+device+'\n'+challenge.nonce+'\n'+body).digest('hex');
 const response=await fetch('http://127.0.0.1:5063/api/v1/device/local-exchange',{method:'POST',headers:{'Content-Type':'application/json','X-Device-ID':device,'X-Local-Nonce':challenge.nonce,'X-Local-Signature':proof},body});assert.equal(response.status,200);assert.equal((await response.json()).receipt,'PERSISTED');
}
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
 const ctx=await browser.newContext(),page=await ctx.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const login=await ctx.request.get(base+'/login'),csrf=(await login.text()).match(/data-csrf="([^"]+)"/)[1];
 assert((await ctx.request.post(base+'/api/auth/login',{headers:{'X-CSRF-Token':csrf},data:{username:'admin',password:'fixture-only-admin-123'}})).ok());
 await publish(24.1);await page.goto(base+'/');await page.waitForFunction(()=>gateway.socket?.connected);
 const card='.dashboard-node[data-node-id="REFRESH-MASTER"] .sensor-live-card[data-id="temperature"]';await page.locator(card).waitFor();
 await page.locator('#dashboard-search').fill('Refresh Master');
 await page.evaluate(()=>{window.refreshOriginalCard=document.querySelector('.dashboard-node[data-node-id="REFRESH-MASTER"] .sensor-live-card[data-id="temperature"]');});
 await publish(27.4);await page.waitForFunction(sel=>document.querySelector(sel)?.textContent.includes('27.40'),card,{timeout:4000});
 assert(await page.evaluate(sel=>document.querySelector(sel)===window.refreshOriginalCard,card));
 assert.equal(await page.locator('#dashboard-search').inputValue(),'Refresh Master');assert(await page.locator('#dashboard-search').evaluate(el=>el===document.activeElement));
 console.log('PASS: signed local TCP -> committed SQLite -> Socket.IO -> live sensor card; DOM identity, search and focus preserved');
 await page.evaluate(()=>gateway.socket.removeAllListeners('telemetry_update'));
 await publish(28.6);await page.waitForFunction(sel=>document.querySelector(sel)?.textContent.includes('28.60'),card,{timeout:9000});
 assert(await page.evaluate(()=>gateway.socket.connected));assert((await page.locator(card+' .sensor-history-chart circle title').allTextContents()).some(t=>t.includes('28.60')));console.log('PASS: snapshot reconciliation updates readings even with connected socket and missed telemetry event');
 await page.route('**/api/live/snapshot',r=>r.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'fixture outage'})}));
 await page.locator('#dashboard-refresh').click();await page.waitForFunction(()=>document.getElementById('dashboard-live-indicator').textContent.includes('failed'));
 assert((await page.locator(card).textContent()).includes('28.60'));await page.unroute('**/api/live/snapshot');
 await page.evaluate(()=>{window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}));window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}));});
 await page.waitForFunction(()=>gateway.socket.connected);await publish(29.7);await page.waitForFunction(sel=>document.querySelector(sel)?.textContent.includes('29.70'),card,{timeout:9000});
 console.log('PASS: refresh failure retains readings and simulated back/forward restoration resumes socket and polling');
 await page.goto(base+'/sensors');await page.locator('#sensor-node').selectOption(device);await publish(30.2);
 await page.waitForFunction(()=>document.getElementById('sensor-management-rows').textContent.includes('30.20'),null,{timeout:9000});console.log('PASS: Sensors management receives live local readings');
 await page.goto(base+'/nodes');await page.locator('#node-search').fill('Refresh Master');
 const rename=await ctx.request.put(base+'/api/nodes/'+device,{headers:{'X-CSRF-Token':(await page.locator('meta[name="sensor-csrf"]').getAttribute('content'))},data:{name:'Refresh Master Updated',communication_type:'LoRa',node_address:'1',enabled:true}});assert(rename.ok(),await rename.text());
 await page.waitForFunction(()=>document.getElementById('nodes-table').textContent.includes('Refresh Master Updated'),null,{timeout:9000});
 assert.equal(await page.locator('#node-search').inputValue(),'Refresh Master');console.log('PASS: Nodes background refresh preserves search');
 for(const route of ['/communication','/system','/system-overview','/logs','/firmware','/mqtt','/local-ip','/command-center','/chat','/accounts']){const response=await page.goto(base+route);assert.equal(response.status(),200);await page.waitForTimeout(250);}
 assert.deepEqual(errors,[]);console.log('PASS: all monitoring/settings routes loaded without browser exceptions');
 await ctx.close();
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
