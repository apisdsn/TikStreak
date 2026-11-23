// Menjalankan semua *.spec.js berurutan; gagal bila ada baris "FAIL ", kode keluar != 0, atau ringkasan error.
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const only = process.argv[2];
const specs = fs.readdirSync(__dirname).filter((f) => f.endsWith('.spec.js') && (!only || f.includes(only))).sort();
let bad = 0;
for (const f of specs) {
  const t0 = Date.now();
  const r = spawnSync('node', [path.join(__dirname, f)], { encoding: 'utf8', timeout: 600000, env: { ...process.env, NODE_PATH: process.env.NODE_PATH || path.join(__dirname, 'node_modules') } });
  const out = (r.stdout || '') + (r.stderr || '');
  const lines = out.split('\n');
  const fails = lines.filter((l) => /^FAIL /.test(l) || /^FAILS (?!\[\])/.test(l) || /^(BAD|ERR) \[.+\]/.test(l) || /^ERRS (?!none)/.test(l));
  const ok = lines.filter((l) => /^ok /.test(l)).length;
  const good = r.status === 0 && !fails.length;
  if (!good) { bad++; console.log(out.slice(-3000)); }
  console.log(`${good ? 'PASS' : 'FAIL'} ${f} (${ok} checks, ${((Date.now() - t0) / 1000).toFixed(0)}s)`);
}
console.log(bad ? `${bad} spec(s) failed` : 'all UI specs passed');
process.exit(bad ? 1 : 0);
