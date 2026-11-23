(() => {
"use strict";
const $ = (id) => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
const LANG_KEY = "bara_lang", THEME_KEY = "bara_theme";
const DICT = {
id: {
navLabel: 'Navigasi Utama', langLabel: 'Bahasa', themeLabel: 'Ganti Tema', login: 'Masuk', previewLabel: 'Contoh Tampilan Panel Bara',
skip: 'Lewati ke Konten Utama', title: 'Bara · Penjaga Streak TikTok', desc: 'Bara mengirim pesan streak TikTok setiap hari sesuai jadwal, lengkap dengan bukti terkirim dan notifikasi Discord atau Telegram.',
nFeat: 'Fitur', nHow: 'Cara Kerja', nSafe: 'Keamanan', nFaq: 'FAQ',
eyebrow: 'Penjaga Streak TikTok',
h1a: 'Streak Tetap Menyala,', h1b: 'Walau Anda Lupa.',
lead: 'Bara Mengirim Pesan Streak ke Teman TikTok Anda Setiap Hari Sesuai Jadwal, Lengkap dengan Bukti Terkirim dan Notifikasi ke Discord atau Telegram.',
ctaMain: 'Masuk ke Panel', ctaHow: 'Lihat Cara Kerja', ctaDocs: 'Panduan Pasang',
tr1: 'Berjalan di Server Sendiri', tr2: 'Cookie Terenkripsi', tr3: 'Tanpa Menyimpan Kata Sandi TikTok',
wNext: 'Jadwal Berikutnya', wNextSub: 'Malam · Semua Kontak (4)', wMsg: 'Pesan:', wLeft: 'Sisa Waktu',
wStreak: 'Hari Beruntun', wNotif: 'Laporan Terkirim', wNotifSub: 'Discord · 4/4 Kontak', w7: '7 Hari Terakhir', wGood: 'Hari Lancar',
strip: [{a: '24/7', b: 'Jadwal Berjalan Otomatis'}, {a: '8 Jadwal', b: 'per Akun, Kontak Bisa Dipilih'}, {a: '100 Akun', b: 'dengan Antrean Browser'}, {a: 'ID / EN', b: 'Tema Terang dan Gelap'}],
kFeat: 'Fitur', hFeat: 'Semua yang Dibutuhkan untuk Menjaga Api Tetap Hidup', sFeat: 'Dari Jadwal sampai Bukti Terkirim, Bara Mengurus Semuanya dari Satu Panel.',
fQueueT: 'Antrean Pintar, Bukan Kirim Membabi Buta', fQueueB: 'Satu Browser Melayani Banyak Akun secara Bergiliran dengan Jeda Acak. Bara Memperkirakan Waktu Selesai dan Memberi Peringatan Jika Antrean Bisa Lewat Tengah Malam.',
kHow: 'Cara Kerja', hHow: 'Tiga Langkah, Lalu Lupakan',
steps: [
{n: '1', t: 'Hubungkan Akun TikTok', b: 'Login Langsung dari Panel Lewat Browser Server, atau Tempel Cookie dengan Panduan Langkah demi Langkah.', tag: 'Sekali Saja'},
{n: '2', t: 'Pilih Kontak dan Jam', b: 'Tambahkan Teman yang Ingin Dijaga Streak-nya, Lalu Atur Jam Kirim, Pesan, dan Penerima untuk Setiap Jadwal.', tag: '± 2 Menit'},
{n: '3', t: 'Bara Mengirim Setiap Hari', b: 'Pesan Terkirim Sesuai Jadwal. Anda Menerima Laporan Lengkap dengan Bukti di Discord atau Telegram.', tag: 'Otomatis'}],
kSafe: 'Keamanan & Privasi', hSafe: 'Data Anda Tetap di Server Anda', sSafe: 'Bara Dipasang di Server atau Home Server Sendiri dengan Docker. Tidak Ada Layanan Pihak Ketiga yang Menyimpan Sesi Anda.',
safe: [
{t: 'Kata Sandi TikTok Tidak Pernah Disimpan', b: 'Hanya Cookie Sesi yang Disimpan, Terenkripsi dengan Kunci Milik Anda.'},
{t: 'Setiap Pengguna Hanya Melihat Akunnya', b: 'Admin Mengelola Pengguna, Bukan Isi Akun Orang Lain.'},
{t: 'Kata Sandi Panel Di-Hash', b: 'PBKDF2 dengan Salt, Sesi Login Bisa Dicabut Kapan Saja.'},
{t: 'Bisa di Balik Cloudflare atau Caddy', b: 'HTTPS Otomatis dan Perlindungan Coba-Coba Login.'}],
termLabel: 'Contoh Perintah Pemasangan', term1: 'Pasang di Server Sendiri', term2: 'Buka Panel', term3: 'Buat Admin Pertama',
hFaq: 'Pertanyaan yang Sering Muncul',
faq: [
{q: 'Apakah Kata Sandi TikTok Saya Disimpan?', a: 'Tidak. Saat Login Lewat Browser Server, Kata Sandi Diketik Langsung ke Halaman TikTok. Bara Hanya Menyimpan Cookie Sesi yang Terenkripsi.', open: true},
{q: 'Bagaimana Jika Cookie Kedaluwarsa?', a: 'Bara Memeriksa Cookie Secara Berkala dan Mengirim Notifikasi Jika Perlu Login Ulang, Jauh Sebelum Jadwal Berikutnya.', open: false},
{q: 'Apakah Akun Bisa Dibanned?', a: 'Tidak Ada Jaminan. Bara Mengirim dengan Jeda Acak dan Perilaku seperti Manusia, Namun Otomasi Tetap Berisiko. Gunakan dengan Bijak untuk Akun Pribadi.', open: false},
{q: 'Berapa Spesifikasi Server yang Dibutuhkan?', a: 'RAM 2 GB Cukup untuk Satu Browser (± 27 Akun per Jam). RAM 4 GB untuk Dua Browser Sekaligus.', open: false},
{q: 'Apakah Bisa Dipakai Bersama Teman?', a: 'Bisa. Admin Membuat Akun Pengguna, dan Setiap Pengguna Mengelola Akun TikTok serta Notifikasinya Sendiri.', open: false}],
ctaT: 'Jangan Biarkan Api Padam Lagi.', ctaB: 'Pasang Bara Sekali, dan Streak Anda Terjaga Setiap Hari.',
disclaimer: 'Tidak Berafiliasi dengan TikTok', footLabel: 'Tautan Footer'
},
en: {
navLabel: 'Main Navigation', langLabel: 'Language', themeLabel: 'Toggle Theme', login: 'Log In', previewLabel: 'Bara Panel Preview',
skip: 'Skip to Main Content', title: 'Bara · TikTok Streak Keeper', desc: 'Bara sends your TikTok streak messages every day on schedule, with proof of delivery and Discord or Telegram reports.',
nFeat: 'Features', nHow: 'How It Works', nSafe: 'Security', nFaq: 'FAQ',
eyebrow: 'Your TikTok Streak Keeper',
h1a: 'Keep the Streak Alive,', h1b: 'Even When You Forget.',
lead: 'Bara Sends Streak Messages to Your TikTok Friends Every Day on Schedule, with Proof of Delivery and Reports to Discord or Telegram.',
ctaMain: 'Open the Panel', ctaHow: 'See How It Works', ctaDocs: 'Install Guide',
tr1: 'Runs on Your Own Server', tr2: 'Encrypted Cookies', tr3: 'TikTok Password Never Stored',
wNext: 'Next Schedule', wNextSub: 'Night · All Contacts (4)', wMsg: 'Message:', wLeft: 'Time Left',
wStreak: 'Day Streak', wNotif: 'Delivery Report', wNotifSub: 'Discord · 4/4 Contacts', w7: 'Last 7 Days', wGood: 'Good Days',
strip: [{a: '24/7', b: 'Schedules Run Automatically'}, {a: '8 Schedules', b: 'per Account, Pick Recipients'}, {a: '100 Accounts', b: 'with a Browser Queue'}, {a: 'ID / EN', b: 'Light and Dark Themes'}],
kFeat: 'Features', hFeat: 'Everything You Need to Keep the Fire Going', sFeat: 'From Schedules to Proof of Delivery, Bara Handles It All from One Panel.',
fQueueT: 'A Smart Queue, Not Blind Blasting', fQueueB: 'One Browser Serves Many Accounts in Turn with Random Pauses. Bara Estimates Finish Times and Warns You if the Queue Could Run Past Midnight.',
kHow: 'How It Works', hHow: 'Three Steps, Then Forget About It',
steps: [
{n: '1', t: 'Connect Your TikTok Account', b: 'Log In Right from the Panel via the Server Browser, or Paste a Cookie with a Step-by-Step Guide.', tag: 'Just Once'},
{n: '2', t: 'Pick Contacts and Times', b: 'Add the Friends Whose Streaks You Want to Keep, Then Set the Time, Message, and Recipients for Each Schedule.', tag: '± 2 Minutes'},
{n: '3', t: 'Bara Sends Every Day', b: 'Messages Go Out on Schedule. You Get a Full Report with Proof on Discord or Telegram.', tag: 'Automatic'}],
kSafe: 'Security & Privacy', hSafe: 'Your Data Stays on Your Server', sSafe: 'Bara Runs on Your Own Server or Home Server with Docker. No Third-Party Service Holds Your Sessions.',
safe: [
{t: 'TikTok Password Is Never Stored', b: 'Only the Session Cookie Is Kept, Encrypted with Your Own Key.'},
{t: 'Each User Sees Only Their Accounts', b: 'Admins Manage Users, Not Other People’s Accounts.'},
{t: 'Panel Passwords Are Hashed', b: 'PBKDF2 with Salt, and Sessions Can Be Revoked Anytime.'},
{t: 'Works Behind Cloudflare or Caddy', b: 'Automatic HTTPS and Brute-Force Login Protection.'}],
termLabel: 'Example Install Commands', term1: 'Install on Your Own Server', term2: 'Open the Panel', term3: 'Create the First Admin',
hFaq: 'Frequently Asked Questions',
faq: [
{q: 'Is My TikTok Password Stored?', a: 'No. When You Log In via the Server Browser, You Type It Straight into TikTok. Bara Only Keeps an Encrypted Session Cookie.', open: true},
{q: 'What if the Cookie Expires?', a: 'Bara Checks Cookies Regularly and Notifies You When a Re-Login Is Needed, Well Before the Next Schedule.', open: false},
{q: 'Can My Account Get Banned?', a: 'There Is No Guarantee. Bara Uses Random Pauses and Human-Like Behavior, but Automation Is Still Risky. Use It Wisely on Personal Accounts.', open: false},
{q: 'What Server Specs Do I Need?', a: '2 GB of RAM Is Enough for One Browser (About 27 Accounts per Hour). 4 GB for Two Browsers at Once.', open: false},
{q: 'Can I Share It with Friends?', a: 'Yes. The Admin Creates User Accounts, and Each User Manages Their Own TikTok Accounts and Notifications.', open: false}],
ctaT: 'Never Let the Fire Go Out Again.', ctaB: 'Set Up Bara Once, and Your Streaks Stay Alive Every Day.',
disclaimer: 'Not Affiliated with TikTok', footLabel: 'Footer Links'
}
};
const DAYS = { id: ['Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min', 'Sen'], en: ['Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Mon'] };
const ICON = {
cal: 'M7 3v4M17 3v4M3 9h18M5 5h14a2 2 0 012 2v12a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2z',
check: 'M9 12l2 2 4-4M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z',
bell: 'M6 8a6 6 0 1112 0c0 7 3 8 3 8H3s3-1 3-8M10 20a2 2 0 004 0',
users: 'M9 11a4 4 0 100-8 4 4 0 000 8zM2 21c.6-3.8 3.4-6 7-6s6.4 2.2 7 6M16 3.5a4 4 0 010 7M18 15c2 .6 3.4 2.4 4 6',
key: 'M15 7a4 4 0 11-3.9 4.9L3 20v-3h3v-3h3l1.1-1.1A4 4 0 0115 7z'
};
const FEAT = {
id: [
{t: 'Jadwal Fleksibel', b: 'Hingga 8 Jadwal per Akun dengan Pesan dan Penerima Berbeda. Jadwal yang Terlewat Dikejar Sampai 3 Jam.', i: 'cal', c: '#0A84FF'},
{t: 'Bukti Setiap Kirim', b: 'Setiap Pesan Diverifikasi: Kolom Chat Kosong, Gelembung Pesan Muncul, dan Jam di Daftar Chat Ikut Berubah.', i: 'check', c: '#34C759'},
{t: 'Notifikasi Discord & Telegram', b: 'Laporan Siapa Saja yang Terkirim, Lengkap dengan Tangkapan Layar Jika Diinginkan.', i: 'bell', c: '#BF5AF2'},
{t: 'Banyak Akun & Pengguna', b: 'Peran Admin dan Pengguna. Setiap Orang Mengelola Akun TikTok dan Notifikasinya Sendiri.', i: 'users', c: '#FF9F0A'},
{t: 'Login dari Panel', b: 'Login TikTok Langsung Lewat Browser Server, Tanpa Menyalin Cookie. Cookie Dicek dan Dijaga Tetap Aktif.', i: 'key', c: '#FF375F'}],
en: [
{t: 'Flexible Schedules', b: 'Up to 8 Schedules per Account with Different Messages and Recipients. Missed Runs Are Caught Up for 3 Hours.', i: 'cal', c: '#0A84FF'},
{t: 'Proof for Every Send', b: 'Each Message Is Verified: the Chat Box Clears, the Bubble Appears, and the Chat List Time Updates.', i: 'check', c: '#34C759'},
{t: 'Discord & Telegram Reports', b: 'See Exactly Who Received a Message, with Screenshots if You Want Them.', i: 'bell', c: '#BF5AF2'},
{t: 'Multiple Accounts & Users', b: 'Admin and User Roles. Everyone Manages Their Own TikTok Accounts and Notifications.', i: 'users', c: '#FF9F0A'},
{t: 'Log In from the Panel', b: 'Sign In to TikTok Right in the Server Browser, No Cookie Copying. Cookies Are Checked and Kept Alive.', i: 'key', c: '#FF375F'}]
};

const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* abaikan */ } },
};
let lang = store.get(LANG_KEY);
if (lang !== "id" && lang !== "en") lang = (navigator.language || "").toLowerCase().startsWith("id") ? "id" : "en";
let theme = store.get(THEME_KEY);
if (theme !== "dark" && theme !== "light") theme = window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";

const el = (tag, props = {}, kids = []) => {
  const n = document.createElement(tag);
  Object.entries(props).forEach(([k, v]) => { if (k === "style") n.style.cssText = v; else if (k in n) n[k] = v; else n.setAttribute(k, v); });
  kids.forEach((k) => n.append(k));
  return n;
};
const svg = (w, attrs, inner) => {
  const s = document.createElementNS(NS, "svg");
  s.setAttribute("width", w); s.setAttribute("height", w); s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("aria-hidden", "true");
  Object.entries(attrs).forEach(([k, v]) => s.setAttribute(k, v));
  s.innerHTML = inner;
  return s;
};
const stroke = { fill: "none", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round" };
const checkSvg = (size, sw, color) => svg(size, { ...stroke, "stroke-width": sw, ...(color ? { stroke: color } : {}) }, '<path d="M5 12l4 4 10-10"/>');
const caret = () => svg(18, { ...stroke, "stroke-width": "2.2" }, '<path d="M6 9l6 6 6-6"/>');

function renderLists() {
  const d = DICT[lang];
  $("days").replaceChildren(...DAYS[lang].map((label, i) => el("div", { className: i === 6 ? "day today" : "day" }, [el("b", {}, [checkSvg(10, "4", "#fff")]), label])));
  $("strip").replaceChildren(...d.strip.map((s) => el("div", {}, [el("strong", { textContent: s.a }), el("span", { textContent: s.b })])));
  const feats = FEAT[lang].map((f) => {
    const fi = el("span", { className: "fi", style: "background:" + f.c }, [svg(22, { ...stroke, stroke: "#fff" }, '<path d="' + ICON[f.i] + '"/>')]);
    return el("div", { className: "fc" }, [fi, el("h3", { textContent: f.t }), el("p", { textContent: f.b })]);
  });
  const logo = svg(44, { style: "flex:none" }, '<path d="M13 2.5C13.6 6 18.5 8.8 18.5 15A6.5 6.5 0 0 1 5.5 15C5.5 11.2 7.6 8.6 9.4 7.2C9.4 9.2 10.3 10.4 11.2 10.9C11 7.8 11.6 4.8 13 2.5Z" fill="none" stroke="#FF8A33" stroke-width="1.3" stroke-linejoin="round"/><path d="M12 15L10.09 13.9" stroke="#fff" stroke-width="1.4" stroke-linecap="round"/><path d="M12 15L14.68 13.45" stroke="#fff" stroke-width="1.1" stroke-linecap="round"/><path d="M12.5 14.13L10.3 17.94" stroke="#FF8A33" stroke-width=".5" stroke-linecap="round"/><circle cx="12" cy="15" r=".7" fill="#FF8A33"/>');
  feats.push(el("div", { className: "fc wide" }, [logo, el("div", {}, [el("h3", { textContent: d.fQueueT }), el("p", { textContent: d.fQueueB })])]));
  $("feat").replaceChildren(...feats);
  $("steps").replaceChildren(...d.steps.map((s) => el("div", { className: "st" }, [el("span", { className: "n", textContent: s.n }), el("h3", { textContent: s.t }), el("p", { textContent: s.b }), el("span", { className: "tag", textContent: s.tag })])));
  $("safe").replaceChildren(...d.safe.map((s) => el("li", {}, [el("b", {}, [checkSvg(15, "2.6")]), el("span", {}, [el("strong", { textContent: s.t }), el("small", { textContent: s.b })])])));
  // FAQ: pertahankan status buka/tutup saat ganti bahasa
  const prev = [...$("faqList").querySelectorAll("details")].map((x) => x.open);
  $("faqList").replaceChildren(...d.faq.map((q, i) => {
    const det = el("details", { className: "fq" }, [el("summary", {}, [q.q, caret()]), el("p", { textContent: q.a })]);
    det.open = prev.length ? prev[i] : q.open;
    return det;
  }));
}

function applyText() {
  const d = DICT[lang];
  document.documentElement.lang = lang;
  document.title = d.title;
  document.querySelector('meta[name="description"]').content = d.desc;
  document.querySelector('meta[property="og:title"]').content = d.title;
  document.querySelector('meta[property="og:description"]').content = d.desc;
  document.querySelectorAll("[data-i18n]").forEach((n) => { if (d[n.dataset.i18n] !== undefined) n.textContent = d[n.dataset.i18n]; });
  document.querySelectorAll("[data-i18n-aria]").forEach((n) => n.setAttribute("aria-label", d[n.dataset.i18nAria]));
  $("ringCap").textContent = d.wLeft;
  $("langId").setAttribute("aria-pressed", String(lang === "id"));
  $("langEn").setAttribute("aria-pressed", String(lang === "en"));
  renderLists();
}

function applyTheme() {
  document.documentElement.dataset.theme = theme;
  const bg = theme === "dark" ? "#000000" : "#F6F7FB";
  document.querySelectorAll('meta[name="theme-color"]').forEach((m) => { m.content = bg; });
  // ikon bulan (tema terang aktif) atau matahari (tema gelap aktif), seperti di aplikasi
  $("themeIcon").innerHTML = theme === "dark"
    ? '<circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6L7 7M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4"/>'
    : '<path d="M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z"/>';
}

function remember() { store.set(LANG_KEY, lang); store.set(THEME_KEY, theme); }
$("langId").addEventListener("click", () => { lang = "id"; store.set(LANG_KEY, lang); applyText(); });
$("langEn").addEventListener("click", () => { lang = "en"; store.set(LANG_KEY, lang); applyText(); });
$("themeBtn").addEventListener("click", () => { theme = theme === "dark" ? "light" : "dark"; store.set(THEME_KEY, theme); applyTheme(); });
// pilihan bahasa dan tema ikut terbawa ke halaman login walau belum pernah diubah manual
document.querySelectorAll("[data-login]").forEach((a) => a.addEventListener("click", remember));

// tautan panduan hanya tampil bila LANDING_DOCS_URL diisi
const docs = $("docsBtn");
const docsUrl = docs.dataset.docs || "";
if (/^https?:\/\//i.test(docsUrl)) { docs.href = docsUrl; docs.classList.remove("hidden"); }

// scroll halus ke bagian halaman (menghormati prefers-reduced-motion)
const reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)");
document.querySelectorAll('a[href^="#"]').forEach((a) => a.addEventListener("click", (e) => {
  const id = a.getAttribute("href").slice(1);
  const target = id && $(id);
  if (!target) return;
  e.preventDefault();
  target.scrollIntoView({ behavior: reduce && reduce.matches ? "auto" : "smooth", block: "start" });
  history.replaceState(null, "", "#" + id);
  if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
  target.focus({ preventScroll: true });
}));

applyTheme();
applyText();
window.__landingReady = true;
})();
