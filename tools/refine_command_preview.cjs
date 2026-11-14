const fs = require('node:fs');
const { chromium } = require('playwright');
const source = 'D:/esp32 selva/command-center-backup-20261015/Gateway/command-center.html';
const css = `
/* Message-card refinement, November 2026. */
.command-chat .command-conversation { background: #f5f7fa; padding: 24px; }
.command-chat .command-message { width: 560px; max-width: 92%; margin-block: 20px; gap: 8px; }
.command-chat .command-bubble { padding: 0; border: 1px solid #dfe5ed; border-radius: 16px; background: white; box-shadow: 0 4px 14px #172b4507; }
.command-chat .outgoing .command-bubble, .command-chat .incoming .command-bubble { border: 1px solid #dfe5ed; background: white; }
.command-chat .command-bubble-head { margin: 0; padding: 14px 20px; background: #fff2f2; color: #b12b3c; font-size: 10px; letter-spacing: .07em; }
.command-chat .incoming .command-bubble-head { background: #eef5fc; color: #245b98; }
.command-chat .command-bubble-head > span:first-child { display: flex; align-items: center; gap: 7px; }
.command-card-icon { width: 18px; height: 18px; flex: 0 0 auto; }
.command-chat .command-bubble h3 { margin: 18px 20px 9px; color: #1b2b41; font-size: 23px; letter-spacing: -.035em; }
.command-card-route { margin: 0 20px 18px; color: #65758b; font: 10px/1.7 ui-monospace,monospace; overflow-wrap: anywhere; }
.command-chat .command-state { border-radius: 20px; font-size: 9px; padding: 4px 8px; letter-spacing: .02em; }
.command-chat .command-bubble > .command-result { margin: 0 20px 16px; padding: 14px 16px; border: 0; border-radius: 10px; background: #f5f8fc; }
.command-chat .command-result h4 { margin: 0 0 8px; font-size: 10px; text-transform: uppercase; letter-spacing: .06em; color: #65758b; }
.command-chat .command-result dl { margin: 0; gap: 10px; }
.command-chat .command-result dd { font-size: 12px; color: #21374f; }
.command-chat .command-request-values dl { grid-template-columns: 1fr; }
.command-chat .command-request-values dd { font-size: 15px; line-height: 1.6; }
.command-chat .command-result-duration { margin: 0 20px 16px; font-size: 11px; font-weight: 600; color: #245b98; }
.command-chat .command-bubble > details { margin: 0 20px; border-top: 1px solid #edf0f4; }
.command-chat .command-bubble summary { padding: 12px 0; color: #526780; font-size: 11px; }
.command-chat .command-bubble details dl { gap: 12px; padding: 0 0 10px; }
.command-chat .command-bubble details dd { color: #243a53; font-size: 11px; }
.command-chat .command-message-actions:empty { display: none; }
.command-chat .command-message-actions { margin: 10px 20px; }
.command-chat .command-message-actions .btn { min-height: 32px; padding: 6px 10px; font-size: 10px; border-radius: 8px; background: #f5f7fa; border-color: #e1e6ee; color: #43566f; }
.command-chat .command-card-footer { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; padding: 12px 20px; margin: 0; background: #fafbfd; border-top: 1px solid #edf0f4; }
.command-chat .command-card-footer code, .command-chat .command-card-footer time { font-size: 9px; color: #718198; }
.command-chat .command-system { margin: 5px auto; max-width: 90%; color: #758397; font-size: 10px; opacity: .85; }
.command-chat .command-system summary { cursor: pointer; }
.command-chat .command-ack { width: fit-content; margin: 10px auto; padding: 7px 13px; border: 1px solid #deebe3; border-radius: 24px; background: #f3faf6; font-size: 9px; }
.command-chat .command-composer { border-top: 1px solid #e1e6ee; padding: 16px 20px; background: white; }
.command-chat .command-send { background: #e7222e; color: white; border-color: #e7222e; border-radius: 9px; }
.command-chat .command-compose-row :is(input,select) { min-height: 40px; border-radius: 9px; }
.command-chat :is(button,summary,input,select):focus-visible { outline: 2px solid #2563eb; outline-offset: 3px; }
[data-theme="dark"] .command-chat .command-conversation { background: #131d2b; }
[data-theme="dark"] .command-chat .command-bubble { background: #202d40; border-color: #3b4c62; }
[data-theme="dark"] .command-chat .command-bubble-head { background: #3b2933; color: #ffb2b8; }
[data-theme="dark"] .command-chat .incoming .command-bubble-head { background: #263d59; color: #b8d8ff; }
[data-theme="dark"] .command-chat .command-bubble :is(h3,dd) { color: #e7effa; }
[data-theme="dark"] .command-chat .command-bubble > .command-result, [data-theme="dark"] .command-chat .command-card-footer { background: #192537; }
[data-theme="dark"] .command-chat .command-composer { background: #202d40; }
@media(max-width:760px) { .command-chat .command-conversation { padding: 14px 10px; } .command-chat .command-message { max-width: 100%; width: 100%; } .command-chat .command-bubble-head { padding: 12px 14px; } .command-chat .command-bubble h3 { margin-left: 14px; } .command-card-route { margin-inline: 14px; } .command-chat .command-bubble > .command-result { margin-inline: 14px; } .command-chat .command-card-footer { padding: 12px 14px; } }
`;
(async () => {
  const browser = await chromium.launch({channel:'msedge',headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  await page.setContent(fs.readFileSync(source,'utf8'));
  await page.evaluate((css) => {
    const style=document.createElement('style');style.id='message-card-refinement';style.textContent=css;document.head.append(style);
    for(const article of document.querySelectorAll('.command-message')) {
      const bubble=article.querySelector('.command-bubble'), incoming=article.classList.contains('incoming');
      const dl=bubble.querySelector(':scope > dl');
      const rows=Array.from(dl?.children||[]);
      const get=(label)=>rows.find(r=>r.querySelector('dt')?.textContent.trim()===label)?.querySelector('dd')?.textContent.trim()||'';
      const route=document.createElement('p');route.className='command-card-route';
      route.textContent=incoming ? `${get('From device')} → ${get('To')}` : `${get('Source')} → ${get('Target')}`;
      bubble.querySelector('h3').after(route);
      const details=document.createElement('details');details.className='command-delivery-details';
      const summary=document.createElement('summary');summary.textContent=incoming?'Acceptance and execution details':'Delivery details · timeout, retries and status';details.append(summary);if(dl)details.append(dl);
      bubble.querySelector('.command-result')?.after(details);
      const heading=bubble.querySelector('.command-bubble-head > span:first-child');
      heading.insertAdjacentHTML('afterbegin',`<svg class="command-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${incoming?'M18 6 6 18M6 8v10h10':'M6 18 18 6M8 6h10v10'}"/></svg>`);
      const directCode=bubble.querySelector(':scope > code');
      let footer=bubble.querySelector('.command-card-footer');if(!footer){footer=document.createElement('footer');footer.className='command-card-footer';bubble.append(footer);}
      if(directCode)footer.append(directCode);
      const time=article.querySelector(':scope > time');if(time)footer.append(time);
    }
    document.documentElement.dataset.messageDesign='refined';
  },css);
  const backup=source.replace('.html','.before-message-redesign.html');if(!fs.existsSync(backup))fs.copyFileSync(source,backup);
  const html=await page.content();fs.writeFileSync(source,html);
  const output='D:/esp32 selva/ESP32_LoRa_Project/docs/design-preview/command-center-refined';fs.mkdirSync(output,{recursive:true});fs.writeFileSync(output+'/command-center.html',html);
  await page.screenshot({path:output+'/desktop.png',fullPage:true});
  const cards=await page.locator('.command-message').count();
  await page.locator('.command-message').last().scrollIntoViewIfNeeded();await page.screenshot({path:output+'/message-cards.png'});
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:output+'/mobile.png',fullPage:true});
  console.log(JSON.stringify({cards,backup,output,mobileOverflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)}));
  await browser.close();
})();
