/* Shared-header regression checks against the isolated gateway fixture. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const routes = ['/', '/nodes', '/sensors', '/command-center', '/communication', '/firmware', '/logs', '/system-overview', '/system', '/chat'];
const base = process.env.GATEWAY_TEST_URL || 'http://127.0.0.1:5057';
(async () => {
    const browser = await chromium.launch({ channel: 'msedge' });
    const results = [];
    fs.mkdirSync('tests/artifacts', { recursive: true });
    try {
        for (const theme of ['light', 'dark']) {
            for (const width of [1440, 768, 360]) {
                const context = await browser.newContext({ viewport: { width, height: 960 } });
                await context.addInitScript(theme => localStorage.setItem('gateway_theme', theme), theme);
                for (const route of routes) {
                    const page = await context.newPage();
                    const errors = [];
                    page.on('pageerror', e => errors.push(e.message));
                    page.on('response', r => { if (r.status() >= 400) errors.push(r.status() + ' ' + r.url()); });
                    const response = await page.goto(base + route);
                    await page.waitForFunction(() => document.getElementById('time').textContent !== '-');
                    await page.waitForTimeout(150);
                    assert.equal(response.status(), 200);
                    assert.equal(await page.locator('.modern-topbar').count(), 1);
                    assert.equal(await page.locator('.global-page-heading').count(), 1);
                    assert.equal(await page.locator('.gateway-banner').count(), route === '/' ? 1 : 0);
                    assert.equal(await page.locator('#gateway-theme-toggle').count(), 0);
                    assert(await page.locator('.header-company-logo img').evaluate(img => img.complete && img.naturalWidth > 0));
                    assert(await page.locator('.brand-orb').getAttribute('src').then(src => src.endsWith('selvarithiks-ad-red-on-white.svg')));
                    assert.equal(await page.locator('#side-navigation .nav-item').count(), 9);
                    assert.equal(await page.locator('html').getAttribute('data-theme'), theme);
                    const bounds = await page.evaluate(() => {
                        const header = document.querySelector('.modern-topbar').getBoundingClientRect();
                        const heading = document.querySelector('.global-page-heading').getBoundingClientRect();
                        const banner = document.querySelector('.gateway-banner')?.getBoundingClientRect();
                        const logo = document.querySelector('.gateway-banner-logo');
                        const items = [...document.querySelector('.topbar-right').children].filter(el => el.getBoundingClientRect().width);
                        return { height: header.height, left: header.left, headingBelow: heading.top >= header.bottom,
                            bannerBelow: !banner || banner.top >= heading.bottom, overflow: document.body.scrollWidth > innerWidth,
                            logoLoaded: !logo || (logo.complete && logo.naturalWidth > 0),
                            controlsFit: items.every(el => el.getBoundingClientRect().right <= innerWidth),
                            titleFits: document.getElementById('page-title').getBoundingClientRect().right <= document.querySelector('.topbar-right').getBoundingClientRect().left };
                    });
                    assert.equal(bounds.height, 60);
                    assert.equal(bounds.left, width >= 768 ? 72 : 0);
                    assert(bounds.headingBelow && bounds.bannerBelow && bounds.logoLoaded && bounds.controlsFit && bounds.titleFits && !bounds.overflow, JSON.stringify({route,width,theme,bounds}));
                    if (route === '/') {
                        assert.equal(await page.locator('.global-page-heading h1').innerText(), 'System Overview');
                        await page.screenshot({ path: 'tests/artifacts/global-header-' + theme + '-' + width + '.png' });
                        const first = await page.locator('#time').innerText();
                        await page.waitForTimeout(1100);
                        assert.notEqual(await page.locator('#time').innerText(), first);
                        await page.waitForFunction(() => gateway.socket?.connected);
                        assert.equal(await page.locator('#global-connection-text').innerText(), 'LIVE');
                        await page.evaluate(() => gateway.socket.disconnect());
                        assert.equal(await page.locator('#global-connection-text').innerText(), 'OFFLINE');
                        await page.evaluate(() => gateway.toggleTheme());
                        assert.equal(await page.locator('html').getAttribute('data-theme'), theme === 'dark' ? 'light' : 'dark');
                    }
                    assert.deepEqual(errors, []);
                    results.push({ route, width, theme, status: 'PASS' });
                    await page.close();
                }
                await context.close();
            }
        }
        const page = await browser.newPage();
        for (const name of ['favicon.svg', 'favicon.ico', 'favicon-192.png', 'favicon-512.png', 'apple-touch-icon.png', 'sr-white-transparent.svg', 'selvarithiks-ad-red-on-white.svg', 'selvarithiks-ad-white-on-red.svg']) {
            assert((await page.request.get(base + '/static/img/' + name)).ok(), name);
        }
        fs.writeFileSync('tests/artifacts/global-header-results.json', JSON.stringify(results, null, 2));
        console.log('PASS: ' + results.length + ' route/theme/viewport checks; clock, socket status, theme switch and eight logo/favicon assets.');
    } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
