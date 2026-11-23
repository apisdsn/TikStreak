// Membuat gambar hero halaman depan dari dasbor sungguhan (data palsu), terang dan gelap, 2x.
// Pakai: cd tests/ui && node landing-shots.js   (butuh python3 dengan Pillow untuk mengonversi ke WebP)
const { launch, server, ROOT } = require('./lib');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const OUT = path.join(ROOT, 'app', 'static', 'img');
fs.mkdirSync(OUT, { recursive: true });
(async () => {
  const srv = await server('setup');
  srv.py('seed_landing.py');
  const b = await launch();
  const sizes = {};
  for (const theme of ['light', 'dark']) {
    const c = await b.newContext({ viewport: { width: 600, height: 1100 }, deviceScaleFactor: 2, colorScheme: theme });
    await c.addInitScript(([t]) => { try { localStorage.setItem('bara_lang', 'id'); localStorage.setItem('bara_theme', t); localStorage.setItem('bara_account', 'main'); } catch (e) { /* abaikan */ } }, [theme]);
    const p = await c.newPage();
    await p.goto(srv.base + '/login');
    await p.fill('#loginUser', 'admin'); await p.fill('#loginPass', 'password1'); await p.click('#loginSubmit');
    await p.waitForSelector('#app:not(.hidden)');
    await p.evaluate(() => fetch('/api/onboarding/dismiss?account=main', { method: 'POST', headers: { 'X-Requested-With': 'bara' } }));
    await p.reload(); await p.waitForSelector('#app:not(.hidden)');
    await p.waitForFunction(() => document.getElementById('streakNum').textContent !== '' && document.querySelectorAll('#weekDays .day').length === 7);
    await p.waitForTimeout(800);
    const box = await p.evaluate(() => {
      const r = ['wNext', 'wStreak', 'wGoal', 'wWeek'].map((i) => document.getElementById(i).getBoundingClientRect());
      const x = Math.min(...r.map((a) => a.left)), y = Math.min(...r.map((a) => a.top));
      return { x, y: y + window.scrollY, width: Math.max(...r.map((a) => a.right)) - x, height: Math.max(...r.map((a) => a.bottom)) - y };
    });
    const png = path.join(srv.tmp, `hero-${theme}.png`);
    await p.screenshot({ path: png, clip: box, fullPage: true });
    const webp = path.join(OUT, `hero-${theme}.webp`);
    const info = execFileSync('python3', ['-c', `
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
for q in (86, 80, 74, 68, 60):
    im.save(sys.argv[2], "WEBP", quality=q, method=6)
    import os
    if os.path.getsize(sys.argv[2]) <= 200 * 1024:
        break
print(im.size[0], im.size[1], os.path.getsize(sys.argv[2]))
`, png, webp]).toString().trim();
    sizes[theme] = info;
    console.log(theme, info);
    await c.close();
  }
  await b.close(); await srv.cleanup();
})().catch((e) => { console.error(e); process.exit(1); });
