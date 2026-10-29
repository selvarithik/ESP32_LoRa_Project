const {chromium}=require("C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const assert=require("node:assert/strict");
(async()=>{
 const browser=await chromium.launch({channel:"msedge",headless:true});
 try{
 const page=await browser.newPage({viewport:{width:1600,height:1100}});
 const errors=[];page.on("pageerror",e=>errors.push(e.message));
 const base="http://127.0.0.1:5057";
 for(let attempt=0;attempt<40;attempt++){
  try{const ready=await page.request.get(base+"/login",{timeout:1000});if(ready.ok())break;}catch(_){}
  if(attempt===39)throw Error("Disposable gateway fixture did not start.");
  await new Promise(resolve=>setTimeout(resolve,250));
 }
 await page.goto(base+"/login");
 await page.locator('#login-form [name=username]').fill('admin');
 await page.locator('#login-form [name=password]').fill('fixture-only-admin-123');
 await page.locator('#signin').click();await page.waitForURL(base+'/');
 await page.goto(base+"/sensors");
 await page.locator("#sensor-add").waitFor({state:"visible"});
 await page.waitForFunction(()=>!document.getElementById("sensor-add").disabled);
 await page.locator("#sensor-add").click();
 const form=page.locator(".sensor-editor");
 await form.locator("[name=parameter_name]").fill("Workshop pressure");
 await form.locator("[name=parameter_id]").fill("PRESS_TEST");
 await form.locator("[name=sensor_id]").fill("PRESS_TEST");
 await form.locator("[name=parameter_type]").fill("Pressure");
 await form.locator("[name=unit]").fill("hPa");
 for(const [icon,color] of Object.entries({fan:'#0d9488',flame:'#dc2626','cloud-rain':'#0284c7',magnet:'#7c3aed',door:'#b45309',weight:'#475569',ruler:'#2563eb',volume:'#be185d',compass:'#4f46e5',beaker:'#15803d'})){await form.locator('[name=icon]').selectOption(icon);assert.equal(await form.locator('[name=color]').inputValue(),color);}
 await form.locator('[name=color]').fill('#112233');await form.locator('[name=icon]').selectOption('fan');assert.equal(await form.locator('[name=color]').inputValue(),'#112233','custom color survives icon choice');
 await form.locator('[name=icon]').selectOption('gauge');
 await form.locator("[name=color]").fill("#0d9488");
 await form.locator("#sensor-wizard-next").click();
 await form.locator("#sensor-wizard-next").click();
 await form.locator("[name=source_field]").fill("raw_pressure");
 await form.locator("#sensor-wizard-next").click();
 await form.locator("[name=display_enabled]").check();
 await form.locator("#sensor-wizard-next").click();
 await form.locator("#sensor-wizard-save").click();
 await form.waitFor({state:"detached"});
 await page.waitForFunction(()=>document.getElementById("sensor-management-rows").textContent.includes("Workshop pressure"));
 const csrf=await page.locator('meta[name="sensor-csrf"]').getAttribute("content");
 const publish=await page.request.post(base+"/api/telemetry",{headers:{"X-CSRF-Token":csrf},data:{node_id:"TEST_001",parameters:{raw_pressure:1010.2}}});assert.equal(publish.status(),200);
 await page.request.post(base+"/api/telemetry",{headers:{"X-CSRF-Token":csrf},data:{node_id:"TEST_001",parameters:{raw_pressure:1011.3}}});
 await page.goto(base+"/");
 await page.locator('.sensor-live-card[data-id="PRESS_TEST"]').waitFor();
 await page.locator('.sensor-live-card[data-id="PRESS_TEST"] .sensor-chart-trigger').click();
 await page.locator(".sensor-readings").waitFor();
 assert.equal(await page.locator("#sensor-detail-select").inputValue(),"PRESS_TEST");
 assert.ok((await page.locator(".sensor-detail-dialog .sensor-axis").textContent()).includes("hPa"));
 assert.ok((await page.locator(".sensor-statistics").textContent()).includes("1010.20"));
 await page.locator("[data-sensor-hours='6']").click();
 await page.locator(".sensor-readings").waitFor();
 await page.locator("#sensor-detail-select").selectOption("rssi");
 await page.locator(".sensor-readings").waitFor();
 assert.ok((await page.locator(".sensor-detail-dialog .sensor-axis").textContent()).includes("dBm"));
 await page.locator(".sensor-readings summary").click();
 assert.ok((await page.locator(".sensor-readings table").textContent()).includes("-89"));
 await page.keyboard.press("Escape");
 await page.locator(".sensor-detail-overlay").waitFor({state:"detached"});
 assert.notEqual(await page.evaluate(()=>document.body.style.overflow),"hidden");
 await page.locator('.sensor-live-card[data-id="PRESS_TEST"] .sensor-chart-trigger').click();
 await page.locator(".sensor-readings").waitFor();
 await page.locator(".sensor-detail-overlay").click({position:{x:3,y:3}});
 await page.locator(".sensor-detail-overlay").waitFor({state:"detached"});
 await page.locator('.sensor-live-card[data-id="PRESS_TEST"] [data-sensor-remove]').click();
 await page.locator('.sensor-live-card[data-id="PRESS_TEST"]').waitFor({state:"detached"});
 await page.locator("#add-sensor-widget-inline").click();
 await page.getByRole("button",{name:"Workshop pressure · Workshop 1 · Add",exact:true}).click();
 await page.locator('.sensor-live-card[data-id="PRESS_TEST"]').waitFor();
 await page.keyboard.press("Escape");
 for(const width of [1600,390]){
  await page.setViewportSize({width,height:1000});
  for(const theme of ["light","dark"]){
   await page.evaluate(t=>gateway.setTheme(t,true),theme);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   await page.locator('.sensor-live-card[data-id="PRESS_TEST"] .sensor-chart-trigger').click();
   await page.locator(".sensor-readings").waitFor();
   assert.equal(await page.locator(".sensor-detail-dialog").evaluate(e=>e.scrollWidth>e.clientWidth),false);
   await page.keyboard.press("Escape");
  }
 }
 assert.deepEqual(errors,[]);
 console.log("PASS: wizard save, real source mapping, card selection, unit axes, ranges, statistics, negative RSSI, Escape/backdrop, removal/re-add, desktop/mobile and both themes; no JavaScript errors.");
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
