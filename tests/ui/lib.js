// Pembantu tes UI: menyalakan aplikasi pada port bebas dengan folder data sementara, dan membuka Chromium.
const { chromium } = require('playwright');
const { spawn, spawnSync, execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const net = require('net');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const SUPPORT = path.join(ROOT, 'tests', 'support');
const PY = process.env.PYTHON || 'python3';
const SH = (process.env.SHOT_DIR || path.join(ROOT, 'tests', 'screenshots')) + path.sep;
fs.mkdirSync(SH, { recursive: true });

const freePort = () => new Promise((res) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const ping = (url) => new Promise((res) => { http.get(url, (r) => { r.resume(); res(r.statusCode === 200); }).on('error', () => res(false)); });

const launch = () => chromium.launch({ args: ['--no-sandbox'] });

class Server {
  constructor(env = {}) {
    this.tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'bara-ui-'));
    this.data = path.join(this.tmp, 'data');
    fs.mkdirSync(this.data, { recursive: true });
    this.env = { QUEUE_JITTER_MIN: '0', QUEUE_JITTER_MAX: '1', ...env };
    this.proc = null;
  }
  async start(extra = {}) {
    this.port = this.port || await freePort();
    this.base = `http://127.0.0.1:${this.port}`;
    const env = { ...process.env, DATA_DIR: this.data, API_KEY: 'testkey123', BROWSER_PATH: chromium.executablePath(), ...this.env, ...extra };
    const log = fs.openSync(path.join(this.tmp, 'server.log'), 'a');
    this.proc = spawn(PY, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(this.port)], { cwd: ROOT, env, stdio: ['ignore', log, log] });
    for (let i = 0; i < 100; i++) { if (await ping(this.base + '/api/health')) return this; await sleep(200); }
    throw new Error('server tidak naik: ' + fs.readFileSync(path.join(this.tmp, 'server.log'), 'utf8').slice(-800));
  }
  async stop() {
    if (!this.proc) return;
    const p = this.proc; this.proc = null;
    await new Promise((r) => { p.once('exit', r); p.kill('SIGTERM'); setTimeout(() => { try { p.kill('SIGKILL'); } catch (e) { /* sudah selesai */ } r(); }, 8000); });
  }
  // mulai ulang (mis. mensimulasikan deploy baru); fresh=true memulai dari folder data kosong
  async restart(extra = {}, { fresh = false, profile = 'legacy' } = {}) {
    await this.stop();
    if (fresh) { fs.rmSync(this.data, { recursive: true, force: true }); fs.mkdirSync(this.data, { recursive: true }); if (profile === 'legacy') execFileSync(PY, [path.join(SUPPORT, 'seed.py'), this.data]); }
    return this.start(extra);
  }
  prepare(profile) { execFileSync(PY, [path.join(SUPPORT, 'prepare.py'), this.base, profile], { stdio: 'inherit' }); }
  // jalankan skrip pembantu Python pada folder data ini (mis. mengisi riwayat)
  py(script, ...args) { return execFileSync(PY, [path.join(SUPPORT, script), ...args], { cwd: ROOT, env: { ...process.env, DATA_DIR: this.data }, stdio: 'inherit' }); }
  async cleanup() { await this.stop(); fs.rmSync(this.tmp, { recursive: true, force: true }); }
}

// profile: legacy (data JSON lama, belum ada admin), setup (admin dibuat), seeded (admin + data contoh), empty (folder kosong)
async function server(profile = 'legacy', env = {}) {
  const s = new Server(env);
  if (profile === 'legacy' || profile === 'setup' || profile === 'seeded') execFileSync(PY, [path.join(SUPPORT, 'seed.py'), s.data]);
  await s.start();
  if (profile === 'setup' || profile === 'seeded') s.prepare(profile);
  return s;
}

// server statis kecil untuk halaman fixture login (tests/fixtures/login)
function fixtureServer() {
  return new Promise((res) => {
    const dir = path.join(ROOT, 'tests', 'fixtures', 'login');
    const srv = http.createServer((req, rsp) => {
      if (req.url.startsWith('/missing')) { rsp.statusCode = 404; return rsp.end(); }
      const f = path.join(dir, req.url.split('?')[0] === '/' ? 'index.html' : req.url.split('?')[0].replace(/\.\./g, ''));
      if (!fs.existsSync(f)) { rsp.statusCode = 404; return rsp.end(); }
      rsp.setHeader('Content-Type', f.endsWith('.png') ? 'image/png' : f.endsWith('.mp4') ? 'video/mp4' : 'text/html');
      rsp.end(fs.readFileSync(f));
    }).listen(0, '127.0.0.1', () => res({ url: `http://127.0.0.1:${srv.address().port}`, close: () => srv.close() }));
  });
}

module.exports = { launch, server, fixtureServer, SH, ROOT, sleep, Server };
