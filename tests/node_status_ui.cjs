/* Browser presentation tests: controlled snapshot states, disposable Flask fixture. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
const ctx=await browser.newContext();const base='http://127.0.0.1:5059';const login=await ctx.request.get(base+'/login');const csrf=(await login.text()).match(/data-csrf="([^"]+)"/)[1];assert((await ctx.request.post(base+'/api/auth/login',{headers:{'X-CSRF-Token':csrf},data:{username:'admin',password:'fixture-only-admin-123'}})).ok());
const snapshot=await (await ctx.request.get(base+'/api/live/snapshot')).json();
for(const theme of ['light','dark'])for(const width of [1440,375]){
 const page=await ctx.newPage();await page.setViewportSize({width,height:960});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(theme=>localStorage.setItem('gateway_theme',theme),theme);
 const value=structuredClone(snapshot),now=Date.now();
 value.nodes[0].last_seen=new Date(now).toISOString();value.nodes[0].status='online';
 value.nodes[1].last_seen=new Date(now-120000).toISOString();value.nodes[1].status='offline';
 value.nodes[2].last_seen=null;value.nodes[2].status='offline';
 await page.route('**/api/live/snapshot',r=>r.fulfill({json:value}));await page.goto(base+'/');
 const on=page.locator('.dashboard-node[data-node-id="TEST_001"]'),off=page.locator('.dashboard-node[data-node-id="TEST_002"]');
 await off.locator('.dashboard-node-error').waitFor();
 assert((await off.locator('.dashboard-node-error').textContent()).includes('No heartbeat for'));
 assert((await off.locator('.sensor-updated').first().textContent()).includes('Last stored reading'));
 assert((await page.locator('.dashboard-node[data-node-id="TEST_003"] .dashboard-node-error').textContent()).includes('No heartbeat received'));
 const colors=await page.evaluate(()=>{const read=sel=>getComputedStyle(document.querySelector(sel));return {green:read('.dashboard-node-status.online').backgroundColor,red:read('.dashboard-node-status.offline').backgroundColor,pulse:read('.dashboard-node-status.online').animationName,offlinePulse:read('.dashboard-node-status.offline').animationName,sensorOffline:read('.dashboard-node[data-node-id="TEST_002"] .sensor-freshness').color,offlineText:read('.dashboard-node-state-pill.offline').color,overflow:document.documentElement.scrollWidth>innerWidth};});
 assert.notEqual(colors.green,colors.red);assert.equal(colors.pulse,'node-heartbeat');assert.equal(colors.offlinePulse,'node-offline-ring');assert.equal(colors.sensorOffline,colors.offlineText);assert.equal(colors.overflow,false);
 await page.emulateMedia({reducedMotion:'reduce'});assert.equal(await on.locator('.dashboard-node-status').evaluate(el=>getComputedStyle(el).animationName),'none');
 // A new heartbeat clears the offline error without navigation.
 value.nodes[1].status='online';value.nodes[1].last_seen=new Date().toISOString();await page.locator('#dashboard-refresh').click();await off.locator('.dashboard-node-state-pill.online').waitFor();assert.equal(await off.locator('.dashboard-node-error').count(),0);
 assert.deepEqual(errors,[]);console.log('PASS '+theme+' '+width+'px: green/red status, offline reasons, last-reading label, pulse, reduced motion, recovery, no overflow');await page.close();
}
await ctx.close();}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
