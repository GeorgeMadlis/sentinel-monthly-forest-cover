// Optional real-browser check. Uses an explicitly supplied local Puppeteer and Chromium.
// node tests/check_bundle_browser.cjs <puppeteer-module> <chromium> <bundle> <screenshot>
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

(async () => {
  const [modulePath, executablePath, bundle, screenshot] = process.argv.slice(2);
  if (![modulePath, executablePath, bundle, screenshot].every(Boolean)) {
    throw new Error('Supply local Puppeteer module, Chromium, bundle directory and screenshot path');
  }
  const puppeteer = require(path.resolve(modulePath));
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'forest-bundle-browser-'));
  let browser;
  try {
    browser = await puppeteer.launch({executablePath, headless: true, userDataDir: profile,
      args: ['--no-sandbox', '--disable-background-networking']});
    const page = await browser.newPage();
    await page.setViewport({width: 1400, height: 1000});
    page.setDefaultTimeout(10000);
    const errors = [], external = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.setRequestInterception(true);
    page.on('request', r => {
      if (/^(file:|data:)/.test(r.url())) r.continue();
      else { external.push(r.url()); r.abort(); }
    });
    const open = async relative => page.goto(pathToFileURL(path.join(bundle, relative)).href);
    await open('index.html');
    assert.match(await page.$eval('body', e => e.textContent), /planned-only/);
    assert.equal(await page.$$eval('a[href^="agents/"]', e => e.length), 7);
    await open('report.html');
    assert.match(await page.$eval('body', e => e.textContent), /NOT full-month composites/);
    await open('maps/index.html');
    await page.waitForFunction(() => window.bundleMap && document.querySelector('.leaflet-control-layers'));
    assert.equal(await page.evaluate(() => Object.keys(window.bundleLayers).length), 2);
    const choose = async year => {
      await page.evaluate(y => {
        const label = [...document.querySelectorAll('.leaflet-control-layers-base label')]
          .find(e => e.textContent.includes(y));
        label.querySelector('input').click();
      }, year);
      await page.waitForFunction(() => [...document.querySelectorAll('img.leaflet-image-layer')]
        .some(e => e.complete && e.naturalWidth > 0));
    };
    await choose('2025');
    assert.match(await page.$eval('img.leaflet-image-layer', e => e.src), /archived-reference.png$/);
    await choose('2026');
    assert.match(await page.$eval('img.leaflet-image-layer', e => e.src), /archived-target.png$/);
    assert.equal(await page.evaluate(() => Object.values(window.bundleMap._layers)
      .filter(l => l.feature?.properties?.id).length), 4);
    await page.screenshot({path: screenshot, fullPage: true});
    assert.deepEqual(errors, []);
    assert.deepEqual(external, []);
    console.log(JSON.stringify({result: 'PASS', protocol: 'file://', network: 'blocked',
      external_requests: external, page_errors: errors, archived_pngs_switched: 2,
      roi_and_control_features: 4, scientific_verification: false}, null, 2));
  } finally {
    if (browser) await browser.close();
    fs.rmSync(profile, {recursive: true, force: true});
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
