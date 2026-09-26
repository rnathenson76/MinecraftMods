// Renders every booklet picture from lego/booklet/steps.json with headless Chromium.
//
//   ROOT=<folder with node_modules/three and lib/ (LDraw library)> node render.mjs
//
// ROOT is served over http on port 8765 with render.html copied into it.
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { fileURLToPath } from 'node:url';

const { chromium } = await import(process.env.PLAYWRIGHT || 'playwright');
const HERE = path.dirname(fileURLToPath(import.meta.url));
const LEGO = path.resolve(HERE, '..', '..');
const ROOT = process.env.ROOT;
const OUT = path.join(LEGO, 'booklet', 'img');
fs.mkdirSync(OUT, { recursive: true });
fs.copyFileSync(path.join(HERE, 'render.html'), path.join(ROOT, 'render.html'));

const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.dat': 'text/plain', '.ldr': 'text/plain' };
const server = http.createServer((req, res) => {
  const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(f, (err, data) => {
    if (err) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' });
    res.end(data);
  });
}).listen(8765);

const data = JSON.parse(fs.readFileSync(path.join(LEGO, 'booklet', 'steps.json'), 'utf8'));
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage();
page.on('console', m => { if (m.type() === 'error') console.log('page:', m.text()); });
await page.goto('http://localhost:8765/render.html');
await page.waitForFunction(() => window.ready === true);
await page.evaluate(c => window.init(c), data.colors);

const save = (name, url) => fs.writeFileSync(path.join(OUT, name), Buffer.from(url.split(',')[1], 'base64'));
const fade = t => t.split('\n').map(l => l.replace(/^1 (\d+) /, (m, c) => `1 ${1000 + +c} `)).join('\n');
const radius = lines => {           // rough size of a set of parts, for steady zoom
  let lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
  for (const l of lines) { const f = l.split(' ').slice(2, 5).map(Number); for (let i = 0; i < 3; i++) { lo[i] = Math.min(lo[i], f[i]); hi[i] = Math.max(hi[i], f[i]); } }
  return Math.hypot(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]) / 2 + 30;
};
const VIEWS = [[-0.6, 0.5, 1.15], [0.6, 0.5, 1.0], [Math.PI - 0.6, 0.5, 0.85], [Math.PI + 0.6, 0.5, 0.85], [-0.6, 1.1, 0.8]];
const only = process.argv[2];

// ---- steps
const sectionFinal = {};
for (const s of data.steps) sectionFinal[s.section + s.asm] = [...s.old, ...s.new];
let n = 0;
for (const [i, s] of data.steps.entries()) {
  const name = `step_${String(i + 1).padStart(3, '0')}.webp`;
  if (only && only !== 'steps') break;
  if (process.env.LIMIT && i >= +process.env.LIMIT) break;
  const minRadius = s.kind === 'build' ? 0.45 * radius(sectionFinal[s.section + s.asm]) : 0;
  const r = await page.evaluate(j => window.renderJob(j), {
    old: fade(s.old.join('\n')), new: s.new.join('\n'), w: 960, h: 720, views: VIEWS, minRadius,
  });
  save(name, r.url); n++;
  if (n % 10 === 0) console.log('step', i + 1, '/', data.steps.length);
}

// ---- part pictures for the callouts
const seen = new Set();
for (const s of data.steps) for (const p of s.parts) seen.add(`${p.part}|${p.color}`);
for (const k of seen) {
  if (only && only !== 'parts') break;
  const [part, color] = k.split('|');
  const c = +color < 0 ? data.any_render : +color;
  const r = await page.evaluate(j => window.renderJob(j), {
    new: `1 ${c} 0 0 0 1 0 0 0 1 0 0 0 1 ${part}.dat`, w: 220, h: 180, az: -0.7, el: 0.55,
  });
  save(`part_${part}_${color}.webp`, r.url);
}

// ---- hero pictures
for (const h of data.heroes || []) {
  const r = await page.evaluate(j => window.renderJob(j), {
    old: h.old ? fade(h.old.join('\n')) : '', new: h.new.join('\n'), w: h.w || 1400, h: h.h || 1000, az: h.az, el: h.el,
  });
  save(`${h.name}.webp`, r.url);
  console.log('hero', h.name);
}
await browser.close();
server.close();
console.log('done');
