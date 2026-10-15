/* Rasterize the supplied square SVG without altering its paths or colors. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
(async () => {
    const directory = path.resolve(__dirname, '../dashboard/static/img');
    const svg = fs.readFileSync(path.join(directory, 'favicon.svg')).toString('base64');
    const browser = await chromium.launch({ channel: 'msedge' });
    try {
        const page = await browser.newPage({ deviceScaleFactor: 1 });
        for (const [size, name] of [[32, null], [192, 'favicon-192.png'], [512, 'favicon-512.png'], [180, 'apple-touch-icon.png']]) {
            await page.setViewportSize({ width: size, height: size });
            await page.setContent('<html><body style="margin:0"><img width="' + size + '" height="' + size + '" src="data:image/svg+xml;base64,' + svg + '"></body></html>');
            await page.locator('img').evaluate(img => img.decode());
            const png = await page.screenshot({ omitBackground: true });
            if (name) fs.writeFileSync(path.join(directory, name), png);
            else {
                // ICO container with one 32px PNG image, supported by modern browsers.
                const header = Buffer.alloc(22);
                header.writeUInt16LE(1, 2);
                header.writeUInt16LE(1, 4);
                header[6] = header[7] = 32;
                header.writeUInt16LE(1, 10);
                header.writeUInt16LE(32, 12);
                header.writeUInt32LE(png.length, 14);
                header.writeUInt32LE(22, 18);
                fs.writeFileSync(path.join(directory, 'favicon.ico'), Buffer.concat([header, png]));
            }
        }
    } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
