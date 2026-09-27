// Deterministic frame export for the animation HTML files in this repo.
//
//   node tools/export-frames.mjs <file.html[?query]> <outdir> [fps=30] [captureStart=4.0] [captureEnd]
//
// Drives headless Chrome with a virtual clock, so every frame is exact regardless of machine
// speed. Time is in seconds of the page's own timeline, which starts at page load: every asset
// holds its cold frame for 5 s, then plays once. captureStart=4.0 keeps one second of the hold
// (the storyboard's "cut the hold to about 1 s"). captureEnd defaults to 5 + T_END + 1.5, where
// T_END is read from the file, so the end frame is held for 1.5 s.
//
// Then assemble with ffmpeg, e.g.
//   ffmpeg -framerate 30 -i out/s1/%05d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart out/s1.mp4
//
// Needs playwright (npm install). Browser: $CHROME_PATH if set, else Google Chrome in /Applications (macOS) if
// present, else Playwright's own Chromium (npx playwright install chromium).
import { chromium } from 'playwright';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const [htmlArg, outdir, fpsArg = '30', startArg = '4.0', endArg] = process.argv.slice(2);
const [html, query = ''] = (htmlArg || '').split('?');   // file.html?move=22 passes a query to the page
if (!html || !outdir) { console.error('usage: node tools/export-frames.mjs <file.html> <outdir> [fps] [captureStart] [captureEnd]'); process.exit(2); }
const fps = +fpsArg, start = +startArg;
const tEndMatch = readFileSync(html, 'utf8').match(/T_END\s*=\s*([\d.]+)/);
const end = endArg ? +endArg : 5 + (tEndMatch ? +tEndMatch[1] : 15) + 1.5;
mkdirSync(outdir, { recursive: true });

const MAC_CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const executablePath = process.env.CHROME_PATH || (existsSync(MAC_CHROME) ? MAC_CHROME : undefined);
const browser = await chromium.launch({ executablePath, headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });

// Virtual clock: replaces rAF, performance.now, Date.now and setTimeout before page scripts run.
await page.addInitScript(() => {
  let vt = 0; const base = Date.now();
  let rafs = []; let rafId = 0;
  let timers = []; let tId = 0;
  window.requestAnimationFrame = cb => { rafs.push({ id: ++rafId, cb }); return rafId; };
  window.cancelAnimationFrame = id => { rafs = rafs.filter(r => r.id !== id); };
  performance.now = () => vt;
  Date.now = () => base + vt;
  window.setTimeout = (fn, ms = 0, ...a) => { timers.push({ id: ++tId, at: vt + ms, fn, a }); return tId; };
  window.clearTimeout = id => { timers = timers.filter(t => t.id !== id); };
  window.__tick = dt => {
    vt += dt;
    const due = timers.filter(t => t.at <= vt).sort((x, y) => x.at - y.at);
    timers = timers.filter(t => t.at > vt);
    for (const t of due) t.fn(...t.a);
    const q = rafs; rafs = [];
    for (const r of q) r.cb(vt);
  };
});

await page.goto(pathToFileURL(html).href + (query ? '?' + query : ''), { waitUntil: 'load' });
await page.addStyleTag({ content: '.wrap{max-width:none!important} html,body{overflow:hidden}' });
await page.evaluate(() => document.fonts.ready);

const dt = 1000 / fps;
let t = 0, n = 0;
while (t < end * 1000 - 1e-6) {
  await page.evaluate(d => window.__tick(d), dt);
  t += dt;
  if (t >= start * 1000) {
    await page.screenshot({ path: `${outdir}/${String(n).padStart(5, '0')}.png`, clip: { x: 0, y: 0, width: 1920, height: 1080 } });
    n++;
  }
}
await browser.close();
console.log(`${html}: ${n} frames at ${fps} fps (${start}s to ${end}s) -> ${outdir}`);
