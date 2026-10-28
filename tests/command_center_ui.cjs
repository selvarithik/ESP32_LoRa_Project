// Real isolated Flask/SQLite backend, software-only Master/Slave transport.
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
 const context=await browser.newContext(),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());
 await page.goto('http://127.0.0.1:5084/login');await page.locator('[name=username]').fill('admin');await page.locator('#password').fill('fixture-only-admin-123');await page.locator('#signin').click();await page.waitForURL('http://127.0.0.1:5084/');
 await page.goto('http://127.0.0.1:5084/command-center');await page.locator('[data-node-id="SIM-COMMAND-SLAVE"]').click();await page.waitForFunction(()=>!document.getElementById('btn-send-command').disabled);
 assert.equal(await page.locator('#param-wifi-pass').count(),0);
 await page.locator('#cmd-type-select').selectOption('PING');await page.locator('#command-quick-input').fill('software-roundtrip');await page.locator('#btn-send-command').click();await page.locator('[data-response-command]').first().waitFor();
 await page.waitForFunction(()=>document.querySelector('[data-response-command]').textContent.includes('COMPLETED'));assert.match(await page.locator('[data-response-command]').first().textContent(),/ACCEPTED/);
 await page.waitForFunction(()=>!document.getElementById('btn-send-command').disabled);await page.locator('#cmd-type-select').selectOption('SET_DEVICE_NAME');await page.locator('#command-arguments-json').fill('{"device_name":"Sim renamed"}');await page.locator('#btn-send-command').click();
 await page.waitForFunction(()=>document.querySelectorAll('[data-response-command]').length===2);await page.waitForFunction(()=>!document.getElementById('btn-send-command').disabled);
 await page.locator('#cmd-type-select').selectOption('SET_TELEMETRY_INTERVAL');await page.locator('#command-arguments-json').fill('{"seconds":1}');await page.locator('#btn-send-command').click();await page.waitForFunction(()=>document.getElementById('command-notice').textContent.includes('INVALID_INTERVAL'));assert.equal(await page.locator('[data-response-command]').count(),2);
 assert.deepEqual(errors,[]);console.log('PASS real Command Center UI -> Flask -> simulated Slave -> separate ACK/RESPONSE -> SQLite -> live UI; validation and secret-input exclusion');await context.close();
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
