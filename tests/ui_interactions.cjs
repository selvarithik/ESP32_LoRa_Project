const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert = require('node:assert/strict');
const base = 'http://127.0.0.1:5057';
const localTime = (offset = 0) => new Date(Date.now() + offset - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, -1);
(async () => {
    const browser = await chromium.launch({ channel: 'msedge' });
    const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
    page.setDefaultTimeout(6000);
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    const post = async (url, data) => {
        const response = await page.request.post(base + url, { data });
        assert(response.ok(), `${url}: ${await response.text()}`);
        return response.json();
    };
    try {
        const context=page.context();const accountPage=await context.request.get(base+'/login');const initialCsrf=(await accountPage.text()).match(/data-csrf="([^"]+)"/)[1]; const login = await context.request.post(base+'/api/accounts/sign-in',{headers:{'X-CSRF-Token':initialCsrf},data:{username:'admin',password:'fixture-only-admin-123'}}); assert(login.ok(), 'Fixture login failed'); const token=(await login.json()).csrf; if(token)await context.setExtraHTTPHeaders({'X-CSRF-Token':token});
        await page.goto(base);
        await page.waitForFunction(() => gateway.socket?.connected);
        await page.locator('.dashboard-sensor-card').first().waitFor();
        const selector = '.dashboard-node[data-node-id="TEST_001"] .dashboard-sensor-card[data-id="temperature"]';
        await page.locator(selector + ' .sensor-chart-trigger').focus();
        await page.evaluate(selector => { window.savedCard = document.querySelector(selector + ' .sensor-chart-trigger'); }, selector);
        const timestamp = localTime();
        await post('/api/telemetry', { node_id: 'TEST_001', timestamp, parameters: { temperature: 33.7 } });
        await page.waitForFunction(selector => document.querySelector(selector + ' .sensor-current strong')?.textContent.includes('33.70'), selector, { timeout: 1500 });
        assert(await page.evaluate(() => savedCard.isConnected && document.activeElement === savedCard));
        await post('/api/telemetry', { node_id: 'TEST_001', timestamp: localTime(-60000), parameters: { temperature: 8 } });
        await page.waitForTimeout(200);
        assert((await page.locator(selector + ' .sensor-current strong').textContent()).includes('33.70'));
        const requests = [];
        page.on('request', r => { if (r.url().includes('/api/')) requests.push(r.url()); });
        await page.waitForTimeout(5300);
        assert.equal(requests.length, 0, 'Polling while connected');
        await page.locator(selector + ' .sensor-chart-trigger').press('Enter');
        await page.locator('.sensor-detail-dialog').waitFor();
        await page.keyboard.press('Escape');
        await page.waitForFunction(() => !document.querySelector('.sensor-detail-overlay'));
        assert(await page.evaluate(() => document.activeElement === savedCard));
        await page.waitForFunction(selector => document.querySelector(selector + ' .sensor-freshness').textContent === 'Stale', selector, { timeout: 12000 });
        await post('/api/telemetry', { node_id: 'TEST_001', timestamp: localTime(), parameters: { temperature: 34.2 } });
        await page.waitForFunction(selector => document.querySelector(selector + ' .sensor-freshness').textContent === 'Live', selector);
        // The current widget catalog persists real sensor visibility rather than synthetic widgets.
        await page.locator(selector + ' .sensor-remove-widget').click();
        await page.locator(selector).waitFor({state:'detached'});
        await page.locator('#add-sensor-widget-inline').click();
        await page.getByRole('dialog', {name:'Add Widget'}).waitFor();
        await page.getByRole('searchbox', {name:'Search configured sensors'}).fill('temperature');
        await page.locator('.sensor-widget-options button').first().click();
        await page.locator(selector).waitFor();
        await page.keyboard.press('Escape');
        assert.equal(await page.locator('#page-title').innerText(), 'Dashboard');
        assert.equal(await page.locator('.gateway-banner').count(), 1);
        // Charts now live in the sensor detail dialog, exercised above.
        await page.reload();
        await page.locator(selector).waitFor(); // Widget visibility survives page reload.
        const rail = page.locator('#side-navigation');
        await page.mouse.move(600, 100);
        await page.waitForTimeout(360);
        assert.equal(Math.round((await rail.boundingBox()).width), 64);
        await rail.hover();
        await page.waitForTimeout(360);
        assert.equal(Math.round((await rail.boundingBox()).width), 224);
        assert(await page.locator('.modern-nav').evaluate(el => el.scrollWidth <= el.clientWidth));
        await page.mouse.move(600, 100);
        await page.waitForTimeout(360);
        assert.equal(Math.round((await rail.boundingBox()).width), 64);
        console.log('PASS live deltas, stable focus/DOM, stale recovery, no polling, popup, widgets, sidebar');

        await page.goto(base + '/nodes');
        await page.locator('#add-node').click();
        await page.locator('#node-form [name="node_id"]').fill('BROWSER_TEST');
        await page.locator('#node-form [name="name"]').fill('Browser sample');
        await page.locator('#node-form [type="submit"]').click();
        await page.getByText('Browser sample', { exact: true }).waitFor();
        await page.locator('[data-node-filter="offline"]').click();
        assert((await page.locator('#nodes-table').textContent()).includes('Browser sample'));
        await page.locator('#node-search').fill('no-match-test');
        assert(!(await page.locator('#nodes-table').textContent()).includes('Browser sample'));
        await page.request.delete(base + '/api/nodes/BROWSER_TEST');
        console.log('PASS node form and filters');

        await page.goto(base + '/sensors');
        await page.locator('.sensor-view').first().waitFor();
        await post('/api/telemetry', { node_id: 'TEST_001', timestamp: localTime(), parameters: { temperature: 32.8 } });
        await page.waitForFunction(() => document.querySelector('#sensor-table').textContent.includes('32.8'));
        await page.locator('.sensor-view').first().click();
        await page.locator('#sensor-drawer.open').waitFor();
        await page.keyboard.press('Escape');
        await page.waitForFunction(() => !document.querySelector('#sensor-drawer').classList.contains('open'));
        console.log('PASS sensor drawer');

        await post('/api/telemetry', { node_id: 'TEST_001', parameters: { temperature: 31 } });
        await page.goto(base + '/command-center');
        await page.locator('.command-node-item[data-node-id="TEST_001"]').click();
        await page.locator('#cmd-type-select').selectOption('PING');
        await page.locator('#command-quick-input').fill('browser sample');
        await page.locator('#btn-send-command').click();
        await page.locator('.command-message').first().waitFor();
        assert(!(await page.locator('#history-list-container').innerText()).includes('undefined'));
        console.log('PASS command send and persisted history');

        await page.goto(base + '/communication');
        await page.locator('[data-v3-tab="settings"]').click();
        await page.locator('#retry-count').fill('4');
        await page.locator('#communication-settings-form [type="submit"],#communication-settings-form .btn-primary').click();
        await page.waitForTimeout(200);
        const network = await page.request.get(base + '/api/communication/settings');
        assert.equal((await network.json()).settings.retry_count, 4);
        console.log('PASS network tabs/settings');

        await page.goto(base + '/firmware');
        await page.locator('[data-v3-tab="settings"]').click();
        await page.locator('#ota-enabled').waitFor({ state: 'visible' });
        await page.locator('#firmware-upload-open').click();
        await page.locator('#firmware-upload-panel.open').waitFor();
        console.log('PASS firmware tabs/upload panel');

        await page.goto(base + '/logs');
        await page.locator('#logs-search').fill('not-in-log-xyz');
        await page.waitForFunction(() => document.querySelector('#logs-table').textContent.includes('No log entries'));
        await page.locator('#logs-clear').click();
        await page.waitForFunction(() => !document.querySelector('#logs-table').textContent.includes('No log entries'));
        console.log('PASS logs filters');

        await page.goto(base + '/system');
        await page.locator('#system-watchdog').fill('91');
        await page.locator('#system-save').click();
        await page.waitForTimeout(500);
        const config = await page.request.get(base + '/api/nodes/TEST_001/config');
        assert.equal((await config.json()).config.watchdog.timeout_s, 91);
        await page.locator('#system-reboot').click();
        await page.locator('#system-confirm-cancel').click();
        console.log('PASS system save/confirmation');

        await page.goto(base + '/chat');
        await page.locator('.chat-row').first().click();
        await page.locator('#chatMessageInput').fill('Browser chat sample');
        await page.locator('#chatSendButton').click();
        await page.getByText('Browser chat sample', { exact: true }).waitFor();
        await page.setViewportSize({ width: 375, height: 850 });
        assert(await page.evaluate(() => document.body.scrollWidth <= innerWidth));
        console.log('PASS chat send/mobile');
        assert.deepEqual(errors, []);
    } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
