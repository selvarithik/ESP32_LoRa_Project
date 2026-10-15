/* Run against tests/gateway_fixture.py. All writes target its temporary database. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const base = process.env.GATEWAY_TEST_URL || 'http://127.0.0.1:5057';
const routes = ['/', '/nodes', '/sensors', '/command-center', '/communication', '/firmware', '/logs', '/system-overview', '/system', '/chat'];
(async () => {
    fs.mkdirSync('tests/artifacts', { recursive: true });
    const browser = await chromium.launch({ channel: process.env.BROWSER_CHANNEL || 'msedge' });
    const results = [];
    try {
        for (const width of [1440, 768, 375]) {
            const context = await browser.newContext({ viewport: { width, height: 960 } });
            for (const route of routes) {
                const page = await context.newPage();
                const errors = [];
                page.on('pageerror', error => errors.push(error.message));
                page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
                const response = await page.goto(base + route);
                await page.waitForTimeout(700);
                const overflow = await page.evaluate(() => ({ body: document.body.scrollWidth > innerWidth + 1, elements: [...document.querySelectorAll('main *, .page-content-v6 *')].filter(el => { const r = el.getBoundingClientRect(); return r.width && r.right > innerWidth + 2 && getComputedStyle(el).position !== 'fixed' && !el.closest('.table-wrap,.drawer,.cmd-modal-overlay,.dashboard-widget-drawer'); }).slice(0, 6).map(el => el.className || el.tagName) }));
                results.push({ width, route, status: response.status(), errors, overflow });
                await page.screenshot({ path: `tests/artifacts/${route.slice(1) || 'live'}-${width}.png`, fullPage: true });
                await page.close();
            }
            await context.close();
        }
        console.log(JSON.stringify(results, null, 2));
        fs.writeFileSync('tests/artifacts/ui-results.json', JSON.stringify(results, null, 2));
        assert(results.every(r => r.status === 200 && !r.errors.length && !r.overflow.body), 'Page smoke failures; inspect ui-results.json');
    } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
