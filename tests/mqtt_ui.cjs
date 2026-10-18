// Real Flask fixture: backend field errors and read-only refresh, no live broker.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict'),base='http://127.0.0.1:5057';
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
 const context=await browser.newContext({viewport:{width:375,height:960}}),page=await context.newPage();
 const loginPage=await context.request.get(base+'/login'),csrf=(await loginPage.text()).match(/data-csrf="([^"]+)"/)[1];
 const login=await context.request.post(base+'/api/auth/login',{headers:{'X-CSRF-Token':csrf},data:{username:'admin',password:'fixture-only-admin-123'}});assert(login.ok());
 await page.goto(base+'/mqtt');await page.locator('#mqtt-host').waitFor();
 assert.equal(await page.locator('#mqtt-fields label').count(),15);
 const before=await (await context.request.get(base+'/api/mqtt')).json();
 await page.locator('#mqtt-host').fill('unsaved.example');await page.locator('#mqtt-refresh').click();await page.waitForFunction(()=>document.getElementById('mqtt-feedback').textContent.startsWith('Status refreshed'));
 assert.equal(await page.locator('#mqtt-host').inputValue(),'unsaved.example');
 const after=await (await context.request.get(base+'/api/mqtt')).json();assert.equal(after.revision,before.revision);assert.equal(after.runtime.state,before.runtime.state);
 await page.locator('#mqtt-ca_cert').fill('invalid certificate');await page.locator('#mqtt-form [type=submit]').click();
 await page.waitForFunction(()=>document.getElementById('mqtt-ca_cert').getAttribute('aria-invalid')==='true');
 assert.equal(await page.locator('#mqtt-ca_cert').evaluate(e=>e===document.activeElement),true);assert.match(await page.locator('#mqtt-error-ca_cert').textContent(),/INVALID_PROFILE/);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 console.log('PASS real Gateway MQTT UI: read-only revision-preserving refresh, unsaved values, backend certificate field error, focus, mobile layout');
 await context.close();
}finally{await browser.close();}})().catch(error=>{console.error(error);process.exitCode=1;});
