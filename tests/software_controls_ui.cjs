/* Real temporary Gateway + HTTP transport + simulated Master/Nodes; no hardware or hosted MQTT. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
const ctx=await browser.newContext();const page=await ctx.newPage();const base='http://127.0.0.1:5080';const errors=[];page.on('pageerror',e=>errors.push(e.message));
const login=await ctx.request.get(base+'/login');const csrf=(await login.text()).match(/data-csrf="([^"]+)"/)[1];assert((await ctx.request.post(base+'/api/auth/login',{headers:{'X-CSRF-Token':csrf},data:{username:'admin',password:'fixture-only-admin-123'}})).ok());
await page.goto(base+'/');await page.locator('.dashboard-node[data-node-id="SIM-NODE-1"]').waitFor();assert((await page.locator('#dashboard-node-list').textContent()).includes('SIMULATED'));
await page.goto(base+'/device-controls');await page.locator('#control-device').selectOption('SIM-NODE-1');
async function completed(){await page.waitForFunction(()=>document.getElementById('control-command-state').textContent.includes('COMPLETED'),null,{timeout:12000});}
await page.locator('#control-config [name=device_name]').fill('SIMULATED Workshop Sensor');await page.locator('#control-config [name=telemetry_seconds]').fill('2');await page.locator('#control-config [type=submit]').click();await completed();assert((await page.locator('#control-result').textContent()).includes('saved'));
await page.locator('#control-sleep [type=submit]').click();await completed();
await page.locator('#control-restart').click();assert((await page.locator('#control-feedback').textContent()).includes('Exact target'));await page.locator('#control-restart-confirm').fill('SIM-NODE-1');await page.locator('#control-restart').click();await completed();await page.waitForFunction(()=>document.getElementById('control-result').textContent.includes('SIMULATED_SOFTWARE_RESET'));
console.log('PASS: normal login -> device controls -> real command queue -> simulated Master/Node -> ACK/response -> displayed result; name, interval, sleep, restart confirmation');
const token=await page.locator('meta[name="sensor-csrf"]').getAttribute('content');const invalid=await ctx.request.post(base+'/api/v1/commands',{headers:{'X-CSRF-Token':token},data:{node_id:'SIM-NODE-1',command_type:'CONFIG_UPDATE',payload:{wifi_dhcp:false,wifi_ip:'192.168.1.0',wifi_subnet:'255.255.255.0',wifi_gateway:'192.168.1.1',wifi_dns:'1.1.1.1'}}});assert.equal(invalid.status(),400);
for(const width of [375,1440]){await page.setViewportSize({width,height:960});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
await page.goto(base+'/mqtt');await page.locator('#mqtt-profile_name').fill('SIMULATED Profile');await page.locator('#mqtt-save-template').click();await page.waitForFunction(()=>document.getElementById('mqtt-saved-profile').textContent.includes('SIMULATED Profile'));await page.locator('#mqtt-select-template').click();await page.waitForFunction(()=>document.getElementById('mqtt-catalog-feedback').textContent.includes('Candidate staged'));
const state=await (await ctx.request.get(base+'/api/mqtt')).json();assert.equal(state.transaction.state,'PENDING');assert(!state.active);assert.equal(state.runtime.acl_status,'UNVERIFIED');assert.equal(await page.locator('#mqtt-confirm').isDisabled(),true);
console.log('PASS: saved MQTT template -> pending candidate only; no active profile, connection or ACL bypass');assert.deepEqual(errors,[]);await ctx.close();
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
