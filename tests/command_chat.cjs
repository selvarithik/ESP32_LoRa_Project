const {chromium}=require("C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const assert=require("node:assert/strict");
(async()=>{
 const browser=await chromium.launch({channel:"msedge",headless:true});
 try{
 const context=await browser.newContext({viewport:{width:1600,height:1000},permissions:["clipboard-read","clipboard-write"]});
 const page=await context.newPage(),base="http://127.0.0.1:5057";const errors=[];page.on("pageerror",e=>errors.push(e.message));
 for(let i=0;i<40;i++){try{if((await page.request.get(base+"/api/status",{timeout:1000})).ok())break;}catch(_){}await new Promise(r=>setTimeout(r,250));}
 async function post(path,data={}){const r=await page.request.post(base+path,{data});assert.ok(r.ok(),path+" "+await r.text());return r.json();}
 await page.goto(base+"/command-center");
 await page.locator(".command-node-item").first().waitFor();
 await page.waitForFunction(()=>!document.getElementById("btn-send-command").disabled);
 await page.selectOption("#cmd-type-select","PING");
 await page.fill("#command-quick-input","fixture echo");
 await page.click("#command-config-toggle");
 await page.fill("#cmd-retries-input","0");
 await page.fill("#cmd-timeout-input","30");
 await page.click("#command-config-toggle");
 await page.click("#btn-send-command");
 await page.locator("[data-command-id]").first().waitFor();
 let record=(await (await page.request.get(base+"/api/commands?node_id=TEST_001")).json()).commands[0];
 const id=record.command_id;assert.equal(record.max_retries,0);assert.equal(record.payload.echo,"fixture echo");
 assert.ok(await page.locator("#btn-send-command").isDisabled());
 assert.equal(await page.locator('[data-command-id="'+id+'"]').count(),1);
 await post("/api/commands/"+id+"/state",{state:"SENT"});
 await post("/api/commands/"+id+"/ack",{node_id:"TEST_001",status:"OK"});
 await page.waitForFunction(id=>document.querySelector('[data-command-id="'+id+'"]').textContent.includes("ACK RECEIVED"),id);
 assert.equal(await page.locator("[data-response-command]").count(),0);
 await post("/api/commands/"+id+"/execute",{node_id:"TEST_001"});
 await post("/api/commands/"+id+"/response",{node_id:"TEST_001",status:"SUCCESS",data:{echo:"fixture echo",temperature:27.4}});
 await page.locator('[data-response-command="'+id+'"]').waitFor();
 await page.locator('[data-copy="'+id+'"]').click();
 const copied=JSON.parse(await page.evaluate(()=>navigator.clipboard.readText()));assert.ok(JSON.stringify(copied).includes("fixture echo"));
 const ids=await page.locator("[data-command-event]").evaluateAll(items=>items.map(x=>x.dataset.commandEvent));assert.equal(new Set(ids).size,ids.length);
 await page.locator('[data-node-id="TEST_002"]').click();
 await page.waitForFunction(()=>document.getElementById("command-active-status").textContent.includes("No active command"));
 assert.equal(await page.locator('[data-command-id="'+id+'"]').count(),0);
 await page.locator('[data-node-id="TEST_001"]').click();
 await page.locator('[data-response-command="'+id+'"]').waitFor();
 await page.reload();await page.locator('[data-response-command="'+id+'"]').waitFor();
 await page.selectOption("#cmd-type-select","STATUS");
 await page.click("#command-config-toggle");await page.fill("#cmd-retries-input","2");await page.click("#command-config-toggle");
 await page.click("#btn-send-command");
 await page.waitForFunction(()=>document.querySelectorAll("[data-command-id]").length===2);
 record=(await (await page.request.get(base+"/api/commands?node_id=TEST_001")).json()).commands[0];const second=record.command_id;
 await post("/api/commands/"+second+"/timeout",{reason:"Fixture timeout"});
 await page.locator('[data-command="'+second+'"][data-action="retry"]').waitFor();
 await page.locator('[data-command="'+second+'"][data-action="retry"]').click();
 await page.locator('[data-command="'+second+'"][data-action="cancel"]').waitFor();
 await page.locator('[data-command="'+second+'"][data-action="cancel"]').click();
 await page.waitForFunction(id=>document.querySelector('[data-command-id="'+id+'"]').textContent.includes("CANCELLED"),second);
 await post("/api/nodes",{node_id:"OFFLINE_TEST",name:"Offline fixture",communication_type:"LoRa"});
 await page.click("#cmd-refresh-btn");await page.locator('[data-node-id="OFFLINE_TEST"]').click();
 await page.waitForFunction(()=>!document.getElementById("btn-send-command").disabled);
 page.once("dialog",d=>d.accept());await page.click("#btn-send-command");
 await page.waitForFunction(()=>document.querySelector("[data-command-id]"));
 const offline=(await (await page.request.get(base+"/api/commands?node_id=OFFLINE_TEST")).json()).commands[0];
 assert.equal(offline.state,"QUEUED");assert.equal(offline.ack_at,null);assert.equal(await page.locator("[data-response-command]").count(),0);
 await post("/api/commands/"+offline.command_id+"/cancel",{});
 for(let i=0;i<35;i++){
  const created=await post("/api/commands",{node_id:"TEST_003",command_type:"PING",payload:{history_index:i}});
  await post("/api/commands/"+created.command.command_id+"/cancel",{});
 }
 await page.locator('[data-node-id="TEST_003"]').click();
 await page.waitForFunction(()=>document.querySelectorAll("[data-command-id]").length>=30);
 await page.locator("#command-conversation").evaluate(e=>{e.scrollTop=0;});
 await page.waitForFunction(()=>document.querySelectorAll("[data-command-id]").length===35);
 const allIds=await page.locator("[data-command-id]").evaluateAll(items=>items.map(e=>e.dataset.commandId));
 assert.equal(new Set(allIds).size,35);
 for(const width of [1600,1024,390]){
  await page.setViewportSize({width,height:900});
  for(const theme of ["light","dark"]){await page.evaluate(t=>gateway.setTheme(t,true),theme);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
 }
 await page.click("#command-back");assert.ok(await page.locator(".command-chat-nodes").isVisible());
 await page.locator('[data-node-id="TEST_001"]').click();assert.ok(await page.locator(".command-chat-workspace").isVisible());
 assert.deepEqual(errors,[]);
 console.log("PASS: actual nodes, command dispatch, zero retries, duplicate guard, ACK without completion, linked response, JSON copy, lifecycle deduplication, node switching, persistence, timeout/retry/cancel, explicit offline queue confirmation, 35-record history pagination, mobile navigation and both themes.");
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
