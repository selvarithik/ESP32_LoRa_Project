// Isolated Flask/SQLite fixture only. Never send these sample packets to a real Gateway.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
const base=process.env.GATEWAY_TEST_URL||'http://127.0.0.1:5084';
if(!/^http:\/\/127\.0\.0\.1:(5084|5057)$/.test(base))throw Error('Isolated fixture port required');
const routes=['/','/nodes','/sensors','/communication','/mqtt','/network','/command-center','/diagnostics','/system-overview','/device-controls','/local-ip','/logs','/system','/firmware','/accounts'];
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const results=[];fs.mkdirSync('tests/artifacts/selva-red',{recursive:true});
 try{
  for(const width of [1366,768,375]){
   const context=await browser.newContext({viewport:{width,height:900}}),p=await context.newPage(),errors=[];
   p.on('pageerror',e=>errors.push(e.message));
   await p.goto(base+'/login');await p.locator('[name=username]').fill('admin');await p.locator('#password').fill('fixture-only-admin-123');await p.locator('#signin').click();await p.waitForURL(base+'/');
   for(const route of routes){
    await p.goto(base+route);await p.locator('.gateway-red').waitFor();await p.evaluate(()=>document.fonts.ready);
    if(route==='/')await p.waitForFunction(()=>document.querySelector('#dashboard-node-list .dashboard-node'));
    const data=await p.evaluate(()=>({path:location.pathname,overflow:document.documentElement.scrollWidth>innerWidth+1,nav:getComputedStyle(document.querySelector('.modern-sidebar')).backgroundColor,active:document.querySelector('.nav-item.active')?getComputedStyle(document.querySelector('.nav-item.active')).backgroundColor:null,links:[...document.querySelectorAll('.modern-nav a')].map(a=>a.getAttribute('href')),header:document.querySelector('#page-title').textContent.trim(),navMotion:getComputedStyle(document.querySelector('.nav-item')).transitionDuration}));
    assert.equal(data.path,route);assert.equal(data.overflow,false,route+' '+width+' overflow');assert.equal(data.nav,'rgb(23, 23, 24)');if(route!=='/accounts')assert.equal(data.active,'rgb(231, 34, 46)',route+' active navigation');
    assert(data.links.includes('/chat'),'Existing navigation must remain available');assert(data.links.includes('/mqtt'));assert(data.links.includes('/logs'));assert(data.links.includes('/local-ip'));assert(data.header);results.push({width,route,...data});
    if(route==='/'){
     assert(await p.locator('#activity-list .dashboard-event-row').count()>0,'Actual fixture logs should populate events');
     if(width===1366){
      const initial=await p.locator('.modern-sidebar').evaluate(e=>e.getBoundingClientRect().width);
      await p.locator('#mobile-menu-btn').click();await p.waitForFunction(()=>document.querySelector('#app-shell').classList.contains('nav-collapsed'));await p.waitForTimeout(300);
      const collapsed=await p.locator('.modern-sidebar').evaluate(e=>e.getBoundingClientRect().width);assert(collapsed<initial);
      await p.locator('#mobile-menu-btn').click();await p.waitForTimeout(300);
     }else{
      await p.locator('#mobile-menu-btn').click();await p.locator('#mobileNavDrawer.open').waitFor();
      await p.waitForTimeout(300);
      assert.equal(await p.locator('.mobile-nav-link.active').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(231, 34, 46)');
      await p.screenshot({path:`tests/artifacts/selva-red/navigation-${width}.png`});await p.locator('.mobile-drawer-close-v6').click();
     }
     await p.screenshot({path:`tests/artifacts/selva-red/dashboard-${width}.png`,fullPage:width===375});
     await p.evaluate(()=>window.scrollTo(0,document.body.scrollHeight));
     await p.waitForFunction(()=>document.querySelector('.geometric-header').classList.contains('is-compact'));
     await p.waitForTimeout(650);
     const bounds=await p.evaluate(()=>{const logo=document.querySelector('.header-company-logo').getBoundingClientRect(),title=document.querySelector('.header-page-group').getBoundingClientRect(),tools=document.querySelector('.topbar-right').getBoundingClientRect();return {logoRight:logo.right,titleLeft:title.left,titleRight:title.right,toolsLeft:tools.left};});
     assert(bounds.titleLeft>=bounds.logoRight-1,'Compact title overlaps NASA logo');assert(bounds.titleRight<=bounds.toolsLeft+1,'Compact title overlaps header controls');
     await p.locator('#widget-sensors').scrollIntoViewIfNeeded();
     await p.screenshot({path:`tests/artifacts/selva-red/telemetry-${width}.png`});
     await p.evaluate(()=>window.scrollTo(0,0));await p.waitForFunction(()=>!document.querySelector('.geometric-header').classList.contains('is-compact'));
     if(width===1366){
      const csrf=await p.locator('meta[name="sensor-csrf"]').getAttribute('content');
      const reply=await context.request.post(base+'/api/telemetry',{headers:{'X-CSRF-Token':csrf},data:{node_id:'TEST_001',parameters:{temperature:31.75,humidity:61.25}}});
      assert(reply.ok(),'Fixture telemetry ingestion');
      await p.waitForFunction(()=>document.querySelector('#dashboard-node-list').textContent.includes('31.75'));
      await p.locator('#dashboard-search').fill('Workshop 1');assert((await p.locator('.dashboard-node').count())>=1);await p.locator('#dashboard-search').fill('');
     }
    }
   }
   assert.deepEqual(errors,[]);await context.close();
  }
  const c=await browser.newContext({viewport:{width:375,height:900},reducedMotion:'reduce'}),p=await c.newPage();
  await p.goto(base+'/login');await p.locator('[name=username]').fill('admin');await p.locator('#password').fill('fixture-only-admin-123');await p.locator('#signin').click();await p.waitForURL(base+'/');
  assert.equal(await p.locator('.nav-item').first().evaluate(e=>getComputedStyle(e).transitionDuration),'0s');await c.close();
  fs.writeFileSync('tests/artifacts/selva-red/results.json',JSON.stringify(results,null,2));
  console.log('PASS 45 real Flask page/viewport checks; black/red navigation, NASA assets, animated desktop collapse/mobile drawer, live fixture telemetry refresh, events, filters, reduced motion and no page errors. No hardware settings changed.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
