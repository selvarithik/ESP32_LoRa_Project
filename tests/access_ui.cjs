// Real Flask fixture and temporary SQLite account DB; never production recovery.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
const base='http://127.0.0.1:5058';
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});try{
for(const width of [360,768,1440]){
 const context=await browser.newContext({viewport:{width,height:960}}),page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/mqtt');assert.equal(new URL(page.url()).pathname,'/login');
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 if(width===360){fs.mkdirSync('tests/artifacts',{recursive:true});await page.screenshot({path:'tests/artifacts/login-mobile.png',fullPage:true});}
 await page.locator('[name=username]').fill('admin');await page.locator('#password').fill('wrong');await page.locator('#visibility').click();assert.equal(await page.locator('#password').getAttribute('type'),'text');await page.locator('#visibility').click();
 await page.locator('#signin').click();await page.waitForFunction(()=>document.getElementById('feedback').textContent.includes('Invalid'));
 await page.locator('#password').fill('fixture-only-admin-123');await page.locator('#signin').click();await page.waitForURL(base+'/');
 await page.goto(base+'/accounts');await page.locator('#account-rows tr').first().waitFor();assert.match(await page.locator('#account-role').textContent(),/creator/);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 if(width===1440)await page.screenshot({path:'tests/artifacts/accounts-desktop.png',fullPage:true});
 await page.locator('#account-new').click();const editor=page.locator('#account-editor');
 await editor.locator('[name=name]').fill('UI account');await editor.locator('[name=username]').fill('ui'+width);await editor.locator('[name=role]').selectOption('user');
 await editor.locator('[name=password]').fill('fixture-user-password');await editor.locator('[name=confirm_password]').fill('fixture-user-password');
 await editor.getByRole('button',{name:'Save',exact:true}).click();await page.waitForFunction(()=>document.getElementById('account-message').textContent==='Account saved.');
 const row=page.locator('#account-rows tr').filter({hasText:'ui'+width});await row.getByRole('button',{name:'Edit',exact:true}).click();
 await editor.locator('[name=name]').fill('Edited UI account');await editor.getByRole('button',{name:'Save',exact:true}).click();await page.waitForFunction(()=>document.getElementById('account-message').textContent==='Account saved.');
 page.once('dialog',d=>d.accept());await row.getByRole('button',{name:'Delete',exact:true}).click();await page.waitForFunction(()=>document.getElementById('account-message').textContent==='Account deleted.');
 await page.goto(base+'/logout');await page.locator('#logout').click();await page.waitForURL('**/login');
 await page.goto(base+'/api/mqtt');assert.match(await page.locator('body').textContent(),/Sign in required/);
 assert.deepEqual(errors,[]);await context.close();console.log(`PASS real Gateway login/accounts UI ${width}px: protected route, validation, visibility, CRUD, logout and API 401`);
}
}finally{await browser.close();}})().catch(error=>{console.error(error);process.exitCode=1;});
