/* Browser-comment regressions, disposable simulator fixture only. */
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
const base='http://127.0.0.1:5084';
(async()=>{
 const browser=await chromium.launch({channel:'msedge'});
 const errors=[],results=[];fs.mkdirSync('tests/artifacts/browser-comments',{recursive:true});
 try{
  const context=await browser.newContext(),page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/login');await page.locator('[name=username]').fill('admin');await page.locator('#password').fill('fixture-only-admin-123');await page.locator('#signin').click();await page.waitForURL(base+'/');
  await page.setViewportSize({width:1071,height:579});
  await page.locator('#dashboard-customize-btn').click();
  await page.locator('[data-target-widget="widget-custom-sensors"]').uncheck();
  await page.locator('[data-target-widget="widget-gateway"]').uncheck();
  await page.locator('#layout-density').selectOption('compact');
  await page.locator('#save-widgets-btn').click();
  await page.reload();
  assert.equal(await page.locator('#widget-custom-sensors').isVisible(),false);
  assert.equal(await page.locator('#widget-gateway').isVisible(),false);
  assert.equal(await page.locator('#dashboard-console').getAttribute('data-density'),'compact');
  await page.locator('#dashboard-customize-btn').click();
  await page.locator('[data-target-widget="widget-custom-sensors"]').check();
  await page.locator('[data-target-widget="widget-gateway"]').check();
  await page.locator('#save-widgets-btn').click();
  assert(await page.locator('#widget-custom-sensors').isVisible());
  await page.locator('#dashboard-customize-btn').click();await page.locator('#reset-widgets-btn').click();await page.locator('#close-widget-drawer').click();
  const routes=['/','/sensors','/command-center','/device-controls','/system-overview','/logs','/diagnostics','/system','/local-ip','/nodes','/mqtt','/network','/communication','/firmware','/accounts','/chat'];
  for(const width of [1440,1071,375]){
   await page.setViewportSize({width,height:width===1071?579:900});
   for(const route of routes){
    const response=await page.goto(base+route);assert.equal(response.status(),200);
    await page.waitForTimeout(350);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,route+' overflow '+width);
    if(route==='/'){
     await page.locator('.dashboard-device-icon').first().waitFor();
     assert(await page.locator('.dashboard-node-state-pill svg').count()>0);
     if(width===1071){
      assert((await page.locator('.communication-path').boundingBox()).height<150);
      assert((await page.locator('.gateway-banner').boundingBox()).height<165);
     }
    }
    if(route==='/logs'){assert.equal(await page.locator('.operations-overview').count(),0);assert.equal(await page.locator('#logs-table').count(),1);}
    if(route==='/diagnostics'){assert.equal(await page.locator('.operations-overview').count(),1);assert.equal(await page.locator('#logs-table').count(),0);}
    if(route==='/sensors'){await page.locator('#sensor-node').selectOption('TEST_001');await page.locator('.sensor-view').first().waitFor();assert((await page.locator('.sensor-view').first().boundingBox()).height>=44);}
    if(['/system','/system-overview','/device-controls'].includes(route))assert.equal(await page.locator('.system-tabs [aria-current]').count(),1);
    if(['/','/sensors','/command-center','/logs','/diagnostics','/system'].includes(route))await page.screenshot({path:'tests/artifacts/browser-comments/'+(route.slice(1)||'dashboard')+'-'+width+'.png'});
    results.push({route,width,status:response.status()});
   }
  }
  assert.deepEqual(errors,[]);
  fs.writeFileSync('tests/artifacts/browser-comments/results.json',JSON.stringify(results,null,2));
  console.log('PASS '+results.length+' route/viewport checks, layout hide/reload/restore/reset, compact panels, status icons, highlighted tabs, sensor View height, Logs/Diagnostics separation, no page errors');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
