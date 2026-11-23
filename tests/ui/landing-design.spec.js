// Halaman depan: tata letak, kontras AA, kapitalisasi, aksesibilitas, tombol salin, gambar hero, dan tangkapan layar.
const { launch, server, SH } = require('./lib');
(async () => {
  const srv = await server('setup'); const B = srv.base; const b = await launch();
  const fails = [], errs = []; const ck = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) fails.push(m); };
  const note = (m) => console.log('NOTE ' + m);
  const hook = (p, tag) => { p.on('pageerror', (e) => errs.push(tag + ' ' + e.message)); p.on('console', (m) => { if (['error', 'warning'].includes(m.type())) errs.push(tag + ' ' + m.text()); }); };
  const COMBOS = []; for (const [w, h] of [[1280, 900], [390, 844]]) for (const th of ['light', 'dark']) for (const lang of ['id', 'en']) COMBOS.push([w, h, th, lang]);

  // ----- fungsi yang dijalankan di halaman
  const PAGE_CHECKS = () => {
    const out = {};
    const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
    const parse = (s) => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
    const over = (top, bottom) => { const a = top[3]; return [0, 1, 2].map((i) => top[i] * a + bottom[i] * (1 - a)).concat([1]); };
    const bgOf = (el) => {
      const chain = []; for (let e = el; e; e = e.parentElement) chain.push(e);
      let base = [255, 255, 255, 1];
      for (const e of chain.reverse()) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c[3] > 0) base = c[3] === 1 ? c : over(c, base); }
      return base;
    };
    document.querySelectorAll('details').forEach((d) => { d.open = true; });
    const rows = []; const seen = new Set();
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n; (n = walker.nextNode());) {
      if (!n.textContent.trim()) continue;
      const el = n.parentElement; if (!el || ['SCRIPT', 'STYLE', 'TITLE'].includes(el.tagName) || el.closest('#bootFail') || el.closest('.skip')) continue;
      const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
      if (cs.display === 'none' || cs.visibility === 'hidden' || r.width === 0) continue;
      let fg = parse(cs.color); const bg = bgOf(el); if (fg[3] < 1) fg = over(fg, bg);
      const L1 = lum(fg), L2 = lum(bg); const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
      const px = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight, 10) >= 700; const large = px >= 24 || (px >= 18.66 && bold);
      const key = (el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : '') + (el.closest('.night-widget') ? '@widget' : el.closest('.code') ? '@code' : '')) + '|' + fg.slice(0, 3).join(',') + '|' + bg.slice(0, 3).join(',');
      if (seen.has(key)) continue; seen.add(key);
      rows.push({ key: key.split('|')[0], fg: fg.slice(0, 3).map(Math.round).join(','), bg: bg.slice(0, 3).map(Math.round).join(','), ratio: Math.round(ratio * 100) / 100, large, text: n.textContent.trim().slice(0, 28) });
    }
    out.contrast = rows;
    out.overflow = document.documentElement.scrollWidth - document.documentElement.clientWidth;
    out.h1 = document.querySelectorAll('h1').length;
    const levels = [...document.querySelectorAll('h1,h2,h3')].map((h) => +h.tagName[1]);
    out.headingsOk = levels.every((l, i) => i === 0 || l <= levels[i - 1] + 1);
    out.landmarks = ['header', 'nav', 'main', 'footer'].every((t) => document.querySelector(t));
    out.emDash = /—/.test(document.body.innerText);
    out.zoomBlocked = /user-scalable\s*=\s*no|maximum-scale\s*=\s*1(\D|$)/.test(document.querySelector('meta[name=viewport]').content);
    // target sentuh: semua kontrol yang terlihat
    out.smallTargets = [...document.querySelectorAll('a[href], button, summary')].filter((e) => !e.closest('.skip') && !e.classList.contains('skip') && !e.closest('#bootFail')).map((e) => { const r = e.getBoundingClientRect(); return { t: (e.textContent || e.id || e.className).trim().slice(0, 20), w: Math.round(r.width), h: Math.round(r.height) }; }).filter((x) => x.w > 0 && (x.w < 44 || x.h < 44));
    out.cursors = [...document.querySelectorAll('a[href], button:not(:disabled), summary')].filter((e) => !e.classList.contains('skip')).filter((e) => getComputedStyle(e).cursor !== 'pointer').map((e) => e.textContent.trim().slice(0, 20));
    out.names = [...document.querySelectorAll('a[href], button, summary')].filter((e) => !(e.getAttribute('aria-label') || e.textContent.trim())).length;
    out.imgs = [...document.querySelectorAll('img')].map((i) => ({ alt: i.alt.length, w: i.getAttribute('width'), h: i.getAttribute('height'), lazy: i.loading, fp: i.getAttribute('fetchpriority') }));
    // judul dan label: Title Case; kalimat: huruf kecil kecuali kata pertama dan nama diri
    const heads = [...document.querySelectorAll('h1, h2, h3, nav a, .btn, .textlink, summary, .copy')].map((e) => e.textContent.trim());
    const sentences = [...document.querySelectorAll('.lead, .intro, .log p, .plain li, .risk, .setup, .install p:not(#docsRow), details p, figcaption, .foot-main p')].map((e) => e.textContent.trim());
    out.heads = heads; out.sentences = sentences;
    return out;
  };
  const CONNECTORS = { id: ['di', 'ke', 'dari', 'dan', 'atau', 'yang', 'untuk', 'dengan', 'pada', 'per', 'lewat', 'lalu', 'agar'], en: ['a', 'an', 'the', 'and', 'or', 'of', 'to', 'in', 'on', 'for', 'at', 'by', 'with', 'via', 'as', 'from', 'per'] };
  const PROPER = /^(Bara|TikTok|Discord|Telegram|Docker|SQLite|AES-256-GCM|SECRET_KEY|PBKDF2|API_KEY|README|RAM|GB|Ctrl\+C|BROWSER_WORKERS|Terlewat|Missed|Cookie|Pengaturan|Settings|FAQ|Jam|Hours|Admin|Admins|Anda|I|\(?SECRET_KEY,?|\.env|rina\.s|dimas_k)[.,:;)?]*$/;
  const titleOk = (s, lang) => s.split(/\s+/).filter(Boolean).every((w, i) => { const core = w.replace(/^[“"'(\[]+|[”"'),.:;!?\]]+$/g, ''); if (!core || /^[^\p{L}]/u.test(core)) return true; const cap = /^\p{Lu}/u.test(core); return i > 0 && CONNECTORS[lang].includes(core.toLowerCase()) ? !cap : cap; });
  const sentenceOk = (s) => { const bad = []; s.split(/(?<=[.!?])\s+/).forEach((sent) => { sent.split(/\s+/).forEach((w, i) => { const core = w.replace(/^[“"'(\[]+/, ''); if (i > 0 && /^\p{Lu}/u.test(core) && !PROPER.test(core) && !/^[A-Z_0-9.\-+]+[,.)]*$/.test(core)) bad.push(core); }); }); return bad; };

  const table = {};
  for (const [w, h, th, lang] of COMBOS) {
    const tag = `${w}-${th}-${lang}`;
    const c = await b.newContext({ viewport: { width: w, height: h }, colorScheme: th, deviceScaleFactor: 1 });
    await c.addInitScript(([l, t]) => { try { localStorage.setItem('bara_lang', l); localStorage.setItem('bara_theme', t); } catch (e) { /* abaikan */ } }, [lang, th]);
    const p = await c.newPage(); hook(p, tag);
    await p.goto(B + '/'); await p.waitForSelector('h1'); await p.waitForTimeout(300);
    const r = await p.evaluate(PAGE_CHECKS);
    ck(r.overflow <= 0, `${tag} no horizontal overflow (${r.overflow})`);
    ck(r.h1 === 1 && r.headingsOk && r.landmarks, `${tag} one h1, no skipped levels, landmarks`);
    ck(!r.emDash, `${tag} no em dash`);
    ck(!r.zoomBlocked, `${tag} zoom not blocked`);
    ck(r.names === 0, `${tag} every control has a name`);
    ck(r.cursors.length === 0, `${tag} cursor:pointer on all controls ${r.cursors.join('|')}`);
    ck(r.imgs.length === 1 && r.imgs[0].alt > 20 && r.imgs[0].w === '1136' && r.imgs[0].h === '1352' && r.imgs[0].lazy !== 'lazy' && r.imgs[0].fp === 'high', `${tag} hero img: alt, size attrs, eager, fetchpriority high`);
    if (w === 390) ck(r.smallTargets.length === 0, `${tag} tap targets >= 44px ${JSON.stringify(r.smallTargets)}`);
    else if (r.smallTargets.length) note(`${tag} controls under 44px at desktop: ${JSON.stringify(r.smallTargets)}`);
    const badTitle = r.heads.filter((s) => !['Yang Disimpan dan Yang Tidak', 'What Bara Keeps, and What It Doesn’t'].includes(s) && !titleOk(s, lang));
    ck(badTitle.length === 0, `${tag} headings/nav/buttons in Title Case ${JSON.stringify(badTitle)}`);
    const badSent = r.sentences.map(sentenceOk).flat();
    ck(badSent.length === 0, `${tag} sentences in sentence case ${JSON.stringify(badSent)}`);
    const low = r.contrast.filter((x) => x.ratio < (x.large ? 3 : 4.5));
    ck(low.length === 0, `${tag} contrast AA on ${r.contrast.length} text styles ${JSON.stringify(low)}`);
    r.contrast.forEach((x) => { const k = `${th}|${x.key}|${x.fg}|${x.bg}`; if (!table[k] || x.ratio < table[k].ratio) table[k] = x; });
    await p.evaluate(() => { document.querySelectorAll('details').forEach((d, i) => { d.open = i === 0; }); window.scrollTo(0, 0); });
    await p.screenshot({ path: SH + `landing-${tag}.png`, fullPage: true });
    await c.close();
  }
  // tabel kontras ringkas per tema (rasio terendah per gaya teks)
  for (const th of ['light', 'dark']) {
    console.log(`CONTRAST-TABLE ${th}`);
    Object.entries(table).filter(([k]) => k.startsWith(th + '|')).map(([, v]) => v).sort((a, z) => a.ratio - z.ratio)
      .forEach((v) => console.log(`CONTRAST ${th} ${v.key.padEnd(24)} fg rgb(${v.fg}) on rgb(${v.bg}) = ${v.ratio}:1${v.large ? ' (large, needs 3)' : ' (needs 4.5)'}`));
  }

  // ----- gambar hero mengikuti tema, tanpa pergeseran tata letak
  {
    const c = await b.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'light' });
    await c.addInitScript(() => { try { localStorage.setItem('bara_lang', 'id'); localStorage.setItem('bara_theme', 'light'); } catch (e) { /* abaikan */ } });
    const p = await c.newPage(); hook(p, 'hero'); await p.goto(B + '/'); await p.waitForSelector('h1');
    await p.waitForFunction(() => document.getElementById('heroImg').complete);
    const box = () => p.evaluate(() => { const r = document.getElementById('heroImg').getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)].join(','); });
    const src = () => p.evaluate(() => document.getElementById('heroImg').currentSrc);
    const b1 = await box(); ck(/hero-light\.webp\?v=/.test(await src()), 'light theme shows hero-light (versioned): ' + await src());
    await p.click('#themeBtn'); await p.waitForFunction(() => /hero-dark/.test(document.getElementById('heroImg').currentSrc)); await p.waitForTimeout(200);
    ck(/hero-dark\.webp/.test(await src()) && await p.evaluate(() => document.getElementById('heroImg').naturalWidth) > 0, 'dark theme swaps to hero-dark and it loads');
    ck((await box()) === b1, 'hero box identical after swap, no layout shift: ' + b1);
    await p.click('#themeBtn'); await p.waitForFunction(() => /hero-light/.test(document.getElementById('heroImg').currentSrc));
    ck(/hero-light/.test(await src()), 'toggle back to light swaps again');
    const sizes = await p.evaluate(async () => Promise.all(['light', 'dark'].map(async (t) => (await fetch(`/static/img/hero-${t}.webp`)).arrayBuffer().then((a) => [t, a.byteLength]))));
    sizes.forEach(([t, n]) => { ck(n <= 200 * 1024, `hero-${t}.webp ${n} bytes <= 200 KB`); note(`hero-${t}.webp = ${n} bytes`); });
    await c.close();
  }

  // ----- tombol salin: berhasil, dan cadangan bila Clipboard API tidak ada
  {
    const c = await b.newContext({ viewport: { width: 1280, height: 900 }, permissions: ['clipboard-read', 'clipboard-write'] });
    await c.addInitScript(() => { try { localStorage.setItem('bara_lang', 'id'); } catch (e) { /* abaikan */ } });
    const p = await c.newPage(); hook(p, 'copy'); await p.goto(B + '/'); await p.waitForSelector('h1');
    const cmd = await p.textContent('#cmd');
    ck(cmd === 'git clone https://github.com/apisdsn/TikStreak\ncd TikStreak\ncp .env.example .env\ndocker compose up -d --build', 'command block holds the four real commands');
    await p.click('#copyBtn'); await p.waitForTimeout(300);
    ck((await p.evaluate(() => navigator.clipboard.readText())) === cmd, 'copy button writes the commands to the clipboard');
    ck((await p.textContent('#copyBtn')) === 'Tersalin' && /disalin/.test(await p.textContent('#copyMsg')), 'success feedback: ' + await p.textContent('#copyBtn') + ' / ' + await p.textContent('#copyMsg'));
    await p.click('#langEn'); await p.waitForTimeout(100);
    await p.waitForFunction(() => document.getElementById('copyBtn').textContent === 'Copy', null, { timeout: 5000 });
    ck(true, 'label returns to Copy after the feedback delay (EN)');
    await c.close();
    const c2 = await b.newContext({ viewport: { width: 1280, height: 900 } });
    await c2.addInitScript(() => { try { localStorage.setItem('bara_lang', 'id'); } catch (e) { /* abaikan */ } Object.defineProperty(navigator, 'clipboard', { value: undefined }); document.execCommand = () => false; });
    const q = await c2.newPage(); hook(q, 'copy-fallback'); await q.goto(B + '/'); await q.waitForSelector('h1');
    await q.click('#copyBtn'); await q.waitForTimeout(200);
    const sel = await q.evaluate(() => getSelection().toString());
    ck(sel === cmd && /Gagal menyalin otomatis/.test(await q.textContent('#copyMsg')) && await q.evaluate(() => document.getElementById('copyMsg').classList.contains('err')), 'fallback: text selected and manual-copy message shown: ' + await q.textContent('#copyMsg'));
    ck((await q.textContent('#copyBtn')) === 'Salin', 'button keeps its label on failure');
    await c2.close();
  }

  // ----- keyboard, fokus, dan kontrol (dasktop)
  {
    const c = await b.newContext({ viewport: { width: 1280, height: 900 } });
    await c.addInitScript(() => { try { localStorage.setItem('bara_lang', 'id'); localStorage.setItem('bara_theme', 'light'); } catch (e) { /* abaikan */ } });
    const p = await c.newPage(); hook(p, 'kbd'); await p.goto(B + '/'); await p.waitForSelector('h1');
    const focusInfo = () => p.evaluate(() => { const e = document.activeElement; const cs = getComputedStyle(e); return { t: (e.id || e.textContent || e.className).trim().slice(0, 24), outline: cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) >= 2 }; });
    const order = [];
    for (let i = 0; i < 13; i++) { await p.keyboard.press('Tab'); order.push(await focusInfo()); }
    note('tab order: ' + order.map((o) => o.t).join(' > '));
    ck(order[0].t === 'Lewati ke Konten Utama' && order.slice(1, 6).map((o) => o.t).join('|') === 'Bara|Cara Kerja|Keamanan|Pasang|FAQ' && order.slice(6, 10).map((o) => o.t).join('|') === 'langId|langEn|themeBtn|Masuk', 'tab order follows the visual order: skip, brand, nav, language, theme, Masuk');
    ck(order.every((o) => o.outline), 'every focused control shows a visible outline');
    await p.focus('.skip'); await p.keyboard.press('Enter'); await p.waitForTimeout(200);
    ck(await p.evaluate(() => document.activeElement.id === 'main' && location.hash === '#main'), 'skip link (Enter) moves focus to main');
    await p.focus('#langEn'); await p.keyboard.press('Space'); ck(await p.getAttribute('#langEn', 'aria-pressed') === 'true', 'Space on EN switches language');
    await p.keyboard.press('Shift+Tab'); await p.keyboard.press('Space');
    ck(await p.getAttribute('#langId', 'aria-pressed') === 'true', 'Space on ID switches back');
    await p.focus('#themeBtn'); await p.keyboard.press('Enter'); ck(await p.evaluate(() => document.documentElement.dataset.theme) === 'dark', 'Enter on the theme button toggles the theme');
    await p.keyboard.press('Enter');
    await p.focus('#faqList details:nth-child(2) summary'); await p.keyboard.press('Enter'); ck(await p.evaluate(() => document.querySelectorAll('#faqList details')[1].open), 'Enter on a FAQ question opens it');
    await p.keyboard.press('Space'); ck(!(await p.evaluate(() => document.querySelectorAll('#faqList details')[1].open)), 'Space on a FAQ question closes it');
    await p.focus('#copyBtn'); await p.context().grantPermissions(['clipboard-read', 'clipboard-write']); await p.keyboard.press('Enter'); await p.waitForTimeout(200);
    ck((await p.textContent('#copyBtn')) === 'Tersalin', 'Enter on the copy button copies');
    await c.close();
  }

  // ----- klik satu per satu (bukti untuk laporan)
  {
    const c = await b.newContext({ viewport: { width: 1280, height: 900 } });
    await c.addInitScript(() => { try { localStorage.setItem('bara_lang', 'id'); localStorage.setItem('bara_theme', 'light'); } catch (e) { /* abaikan */ } });
    const p = await c.newPage(); hook(p, 'click');
    const top = (id) => p.evaluate((i) => Math.round(Math.abs(document.getElementById(i).getBoundingClientRect().top)), id);
    for (const [txt, id] of [['Cara Kerja', 'how-it-works'], ['Keamanan', 'security'], ['Pasang', 'install'], ['FAQ', 'faq']]) {
      await p.goto(B + '/'); await p.waitForSelector('h1'); await p.click(`.links >> text="${txt}"`); await p.waitForTimeout(1100);
      const t = await top(id); ck(t < 40 && (await p.evaluate(() => location.hash)) === '#' + id, `CLICK nav "${txt}" -> #${id} in view (top=${t}px)`);
    }
    await p.goto(B + '/'); await p.waitForSelector('h1'); await p.click('.textlink >> text="Lihat Cara Kerja"'); await p.waitForTimeout(1100);
    ck((await top('how-it-works')) < 40, 'CLICK "Lihat Cara Kerja" -> #how-it-works');
    for (const [sel, name] of [['.nav-bar a[data-login]', 'nav Masuk'], ['.hero a[data-login]', 'hero Masuk ke Panel'], ['.foot a[data-login]', 'footer Masuk']]) {
      await p.goto(B + '/'); await p.waitForSelector('h1'); await p.click(sel); await p.waitForSelector('#login:not(.hidden)');
      ck(new URL(p.url()).pathname === '/login', `CLICK ${name} -> /login with the login form`);
    }
    await p.goto(B + '/'); await p.waitForSelector('h1');
    for (let i = 0; i < 6; i++) { await p.locator('#faqList summary').nth(i).click(); const open = await p.evaluate((n) => document.querySelectorAll('#faqList details')[n].open, i); await p.locator('#faqList summary').nth(i).click(); ck(open !== (await p.evaluate((n) => document.querySelectorAll('#faqList details')[n].open, i)), `CLICK FAQ item ${i + 1} toggles`); }
    await p.click('#langEn'); ck((await p.textContent('h1')).startsWith('Your TikTok Streak Messages') && await p.evaluate(() => document.documentElement.lang) === 'en' && (await p.title()) === 'Bara · TikTok Streak Keeper', 'CLICK EN -> English texts, title, lang');
    await p.click('#langId'); ck((await p.textContent('h1')).startsWith('Pesan Streak TikTok') && await p.evaluate(() => document.documentElement.lang) === 'id', 'CLICK ID -> Indonesian texts and lang');
    await p.click('#themeBtn'); ck(await p.evaluate(() => document.documentElement.dataset.theme) === 'dark', 'CLICK theme -> dark');
    await p.click('#themeBtn'); ck(await p.evaluate(() => document.documentElement.dataset.theme) === 'light', 'CLICK theme -> light');
    await c.close();
  }
  console.log(errs.length ? 'ERRS ' + errs.slice(0, 6).join(' | ') : 'ERRS none');
  console.log(fails.length ? 'FAILS ' + fails.length : 'ALL OK');
  await b.close(); await srv.cleanup();
})().catch((e) => { console.log('FAIL exception ' + (e && e.stack || e)); process.exit(1); });
