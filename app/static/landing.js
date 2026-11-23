(() => {
"use strict";
const $ = (id) => document.getElementById(id);
const LANG_KEY = "bara_lang", THEME_KEY = "bara_theme";

// Kalimat penuh ditulis dengan huruf kapital kalimat; judul, navigasi, tombol, dan label pendek diberi Title Case oleh titleCase()
// (aturan penghubung sama dengan panel). Kunci di VERBATIM ditulis persis seperti yang dimaksud.
const VERBATIM = new Set(["hSafe"]);
const DICT = {
id: {
  skip: "Lewati ke Konten Utama", navLabel: "Navigasi Utama", langLabel: "Bahasa", themeLabel: "Ganti Tema", footLabel: "Tautan Footer",
  title: "Bara · Penjaga Streak TikTok",
  desc: "Bara mengirim pesan streak TikTok setiap hari sesuai jadwal dari server Anda sendiri, dan melapor ke Discord atau Telegram.",
  nHow: "Cara kerja", nSafe: "Keamanan", nInstall: "Pasang", nFaq: "FAQ", login: "Masuk",
  h1: "Pesan streak TikTok terkirim tiap hari, dari server Anda sendiri",
  lead: "Bara mengirim pesan ke kontak TikTok Anda sesuai jadwal dan baru menghitungnya terkirim setelah kolom chat kosong dan gelembung pesan baru muncul.",
  ctaMain: "Masuk ke panel", ctaHow: "Lihat cara kerja",
  heroAlt: "Tangkapan layar dasbor Bara: widget Jadwal Berikutnya pukul 23:00 dengan hitung mundur, widget Hari Beruntun bernilai 14, dan widget 7 Hari Terakhir dengan enam hari terkirim.",
  caption: "Contoh tampilan panel dengan data contoh.",
  hNight: "Satu malam bersama Bara",
  nightIntro: "Ini contoh satu malam untuk jadwal pukul 23:00 dengan empat kontak. Jamnya hanya ilustrasi, sedangkan urutan dan aturannya sesuai cara Bara bekerja.",
  log: [
    ["23:00", "Jadwal jatuh tempo dan masuk antrean. Browser dibuka untuk akun ini dengan cookie sesi yang tersimpan."],
    ["23:01", "Pesan untuk rina.s dikirim. Nama chat dicocokkan lebih dulu, dan pesan dihitung terkirim setelah kolom chat kosong dan gelembung pesan baru muncul. Jam di daftar chat dicatat sebagai bukti tambahan."],
    ["23:02", "Pesan untuk dimas_k gagal tiga kali karena timeout, jadi Bara lanjut ke kontak berikutnya."],
    ["23:04", "Pengiriman selesai dengan 3 dari 4 kontak terkirim. Laporannya masuk ke Discord atau Telegram, dengan screenshot bukti bila opsi itu diaktifkan."],
    ["23:34", "Bara mencoba dimas_k lagi, 30 menit setelah pengiriman pertama. Percobaan ulang berlaku untuk kegagalan sementara seperti timeout dan halaman yang gagal dimuat, maksimal 2 kali."],
  ],
  hRules: "Aturan waktu",
  rules: [
    ["23:50", "Tidak ada percobaan ulang yang dijadwalkan bila perkiraan mulainya lewat jam ini."],
    ["3 Jam", "Jadwal yang terlewat karena server restart atau antrean penuh masih dikejar sampai 3 jam. Setelah itu dicatat sebagai Terlewat dan pemiliknya diberi tahu."],
  ],
  setup: "Untuk mulai, hubungkan akun TikTok lewat browser di server panel atau dengan menempel cookie. Lalu tambahkan kontak, atau impor dari daftar chat TikTok, dan atur jadwal, maksimal 8 per akun.",
  hSafe: "Yang Disimpan dan Yang Tidak", hKept: "Disimpan", hNever: "Tidak pernah dilakukan",
  kept: [
    "Cookie sesi TikTok, terenkripsi AES-256-GCM dengan kunci milik Anda (SECRET_KEY, atau file secret.key yang dibuat otomatis).",
    "Kontak, jadwal, riwayat, dan pengguna, dalam database SQLite di volume server Anda.",
    "Kata sandi panel, sebagai hash PBKDF2 dengan salt. Sesi login bisa dicabut kapan saja.",
  ],
  never: [
    "Kata sandi TikTok. Saat login lewat browser server, Anda mengetiknya langsung ke halaman TikTok.",
    "Sesi Anda di server pihak ketiga. Bara hanya berhubungan dengan TikTok, dan dengan Discord atau Telegram bila Anda mengaktifkannya.",
    "Isi akun pengguna lain untuk admin. Admin mengelola pengguna dan pengaturan global, dan tidak bisa membaca akun, kontak, atau cookie mereka.",
  ],
  risk: "Tidak ada jaminan akun aman dari pembatasan. Bara memberi jeda acak antar pekerjaan dan memakai browser sungguhan, tetapi otomasi tetap berisiko, jadi pakai untuk akun pribadi.",
  hInstall: "Pasang sendiri",
  installIntro: "Bara berjalan di Docker. Empat perintah ini menyalakannya di server Anda.",
  installAfter: "Isi API_KEY di file .env sebelum menjalankan docker compose. Panel lalu terbuka di http://localhost:8000, dan Anda membuat admin pertama di sana.",
  requirements: "RAM 2 GB cukup untuk satu browser, dan 4 GB untuk dua (panduan di README). Perkiraan antrean Bara untuk akun dengan 4 kontak adalah sekitar 2,5 menit per akun, atau sekitar 23 akun per jam untuk satu browser.",
  copy: "Salin", copied: "Tersalin", copyOk: "Perintah sudah disalin.", copyFail: "Gagal menyalin otomatis. Teksnya sudah dipilih, tekan Ctrl+C untuk menyalin.",
  ctaDocs: "Panduan pasang",
  hFaq: "Pertanyaan yang sering muncul",
  faq: [
    ["Apakah kata sandi TikTok saya disimpan?", "Tidak. Saat Anda login lewat browser server, kata sandi diketik langsung ke halaman TikTok. Bara hanya menyimpan cookie sesi dalam bentuk terenkripsi."],
    ["Apa yang terjadi jika cookie kedaluwarsa?", "Bara memeriksa cookie secara berkala (default tiap 12 jam, bisa diubah admin). Bila sesi tidak berlaku lagi, pemilik akun diberi tahu lewat Discord atau Telegram yang sudah diatur, lalu perlu login ulang di tab Cookie."],
    ["Apakah akun saya bisa terkena banned?", "Tidak ada jaminan. Bara memberi jeda acak antar pekerjaan dan memakai browser sungguhan, tetapi otomasi tetap berisiko. Pakai untuk akun pribadi."],
    ["Bagaimana jika sebuah pesan gagal terkirim?", "Kegagalan sementara, seperti timeout atau halaman yang gagal dimuat, diulang 30 menit kemudian, maksimal 2 kali, dan hanya bila perkiraan mulainya sebelum pukul 23:50. Kontak yang tidak ditemukan dan cookie yang tidak valid tidak diulang. Admin bisa mengubah jeda dan batasnya di Pengaturan."],
    ["Berapa spesifikasi server yang dibutuhkan?", "RAM 2 GB cukup untuk satu browser dan 4 GB untuk dua. Jumlah browser diatur lewat BROWSER_WORKERS, dan README menjelaskan panduan lengkapnya."],
    ["Apakah bisa dipakai bersama teman?", "Bisa. Admin membuat akun pengguna, dan tiap pengguna mengelola akun TikTok, kontak, dan notifikasinya sendiri. Admin tidak bisa membaca akun pengguna lain."],
  ],
  footLine: "Sudah punya panel Bara? Masuk untuk mengelola akun, kontak, dan jadwal.",
  disclaimer: "Tidak berafiliasi dengan TikTok",
},
en: {
  skip: "Skip to Main Content", navLabel: "Main Navigation", langLabel: "Language", themeLabel: "Toggle Theme", footLabel: "Footer Links",
  title: "Bara · TikTok Streak Keeper",
  desc: "Bara sends your TikTok streak messages every day on schedule from your own server, and reports to Discord or Telegram.",
  nHow: "How it works", nSafe: "Security", nInstall: "Install", nFaq: "FAQ", login: "Log in",
  h1: "Your TikTok streak messages, sent every day from your own server",
  lead: "Bara sends messages to your TikTok contacts on schedule and only counts them as delivered once the chat box is empty and the new message bubble appears.",
  ctaMain: "Open the panel", ctaHow: "See how it works",
  heroAlt: "Screenshot of the Bara dashboard: the Next Schedule widget at 23:00 with a countdown, the Day Streak widget showing 14, and the Last 7 Days widget with six days delivered.",
  caption: "Panel preview with example data.",
  hNight: "One night with Bara",
  nightIntro: "This is an example night for a 23:00 schedule with four contacts. The times are illustrative, while the order and the rules follow how Bara works.",
  log: [
    ["23:00", "The schedule comes due and joins the queue. A browser opens for this account with its saved session cookie."],
    ["23:01", "The message to rina.s is sent. The chat name is matched first, and the message counts as delivered once the chat box is empty and a new message bubble appears. The time in the chat list is recorded as extra evidence."],
    ["23:02", "The message to dimas_k times out three times, so Bara moves on to the next contact."],
    ["23:04", "The send finishes with 3 of 4 contacts delivered. The report goes to Discord or Telegram, with a proof screenshot when that option is on."],
    ["23:34", "Bara tries dimas_k again, 30 minutes after the first send. Retries apply to temporary failures such as timeouts and pages that fail to load, up to 2 times."],
  ],
  hRules: "Time rules",
  rules: [
    ["23:50", "No retry is scheduled when its estimated start falls after this time."],
    ["3 Hours", "A schedule missed because of a server restart or a full queue is still caught up for up to 3 hours. After that it is recorded as Missed and its owner is notified."],
  ],
  setup: "To start, connect your TikTok account through the browser on the panel's server or by pasting a cookie. Then add contacts, or import them from your TikTok chat list, and set schedules, up to 8 per account.",
  hSafe: "What Bara Keeps, and What It Doesn’t", hKept: "Stored", hNever: "Never stored or done",
  kept: [
    "The TikTok session cookie, encrypted with AES-256-GCM using a key you own (SECRET_KEY, or a secret.key file created automatically).",
    "Contacts, schedules, history, and users, in a SQLite database on your server's volume.",
    "Panel passwords, as PBKDF2 hashes with a salt. Login sessions can be revoked at any time.",
  ],
  never: [
    "Your TikTok password. When you log in through the server browser, you type it straight into the TikTok page.",
    "Your session on any third-party server. Bara only talks to TikTok, and to Discord or Telegram when you turn them on.",
    "Other users' accounts, for admins. Admins manage users and global settings, and cannot read their accounts, contacts, or cookies.",
  ],
  risk: "There is no guarantee that an account stays free of restrictions. Bara adds random pauses between jobs and uses a real browser, yet automation stays risky, so use it for personal accounts.",
  hInstall: "Install it yourself",
  installIntro: "Bara runs in Docker. These four commands start it on your server.",
  installAfter: "Fill in API_KEY in the .env file before running docker compose. The panel then opens at http://localhost:8000, where you create the first admin.",
  requirements: "2 GB of RAM is enough for one browser, and 4 GB for two (guidance from the README). Bara's queue estimates about 2.5 minutes per account with 4 contacts, or about 23 accounts per hour for one browser.",
  copy: "Copy", copied: "Copied", copyOk: "Commands copied.", copyFail: "Automatic copy failed. The text is selected, press Ctrl+C to copy it.",
  ctaDocs: "Install guide",
  hFaq: "Frequently asked questions",
  faq: [
    ["Is my TikTok password stored?", "No. When you log in through the server browser, you type the password straight into the TikTok page. Bara only keeps an encrypted session cookie."],
    ["What happens when the cookie expires?", "Bara checks the cookie regularly (every 12 hours by default, which an admin can change). When the session stops working, the account owner is told through the Discord or Telegram channel they set up, and needs to log in again on the Cookie tab."],
    ["Can my account get banned?", "There is no guarantee. Bara adds random pauses between jobs and uses a real browser, but automation stays risky. Use it for personal accounts."],
    ["What if a message fails to send?", "Temporary failures, such as timeouts or pages that fail to load, are retried 30 minutes later, up to 2 times, and only when the estimated start is before 23:50. Contacts that are not found and invalid cookies are not retried. Admins can change the delay and the limit in Settings."],
    ["What server specs do I need?", "2 GB of RAM is enough for one browser and 4 GB for two. The number of browsers is set with BROWSER_WORKERS, and the README has the full guidance."],
    ["Can I share it with friends?", "Yes. The admin creates user accounts, and each user manages their own TikTok accounts, contacts, and notifications. Admins cannot read other users' accounts."],
  ],
  footLine: "Already have a Bara panel? Log in to manage accounts, contacts, and schedules.",
  disclaimer: "Not affiliated with TikTok",
},
};

// Title Case dengan aturan penghubung yang sama seperti di panel
const CONNECTORS = {
  id: new Set(["di", "ke", "dari", "dan", "atau", "yang", "untuk", "dengan", "pada", "per", "lewat", "lalu", "agar"]),
  en: new Set(["a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "at", "by", "with", "via", "as", "from", "per"]),
};
let lang, theme;
function titleCase(s) {
  let first = true;
  return String(s).split(/(\s+)/).map((w) => {
    if (!w.trim()) return w;
    const core = w.replace(/^[“"'(\[]+|[”"'),.:;!?\]]+$/g, "").toLowerCase();
    const isFirst = first;
    first = /[.!?]$/.test(w);
    if (!isFirst && CONNECTORS[lang].has(core)) return w.replace(/[\p{L}]+/u, core);
    return w.replace(/\p{L}/u, (c) => c.toUpperCase());
  }).join("");
}

const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* abaikan */ } },
};
lang = store.get(LANG_KEY);
if (lang !== "id" && lang !== "en") lang = (navigator.language || "").toLowerCase().startsWith("id") ? "id" : "en";
theme = document.documentElement.dataset.theme === "dark" ? "dark" : "light";

const el = (tag, props = {}, kids = []) => {
  const n = document.createElement(tag);
  Object.entries(props).forEach(([k, v]) => { if (k in n) n[k] = v; else n.setAttribute(k, v); });
  kids.forEach((k) => n.append(k));
  return n;
};

function renderLists() {
  const d = DICT[lang];
  const row = (cls) => ([t, x]) => el("li", {}, [el(t.includes(":") ? "time" : "span", { className: t.includes(":") ? "" : "stamp", textContent: t.includes(":") ? t : titleCase(t) }), el("p", { textContent: x })]);
  $("log").replaceChildren(...d.log.map(row("log")));
  $("rules").replaceChildren(...d.rules.map(([t, x]) => el("li", {}, [el("span", { className: "stamp", textContent: t.includes(":") ? t : titleCase(t) }), el("p", { textContent: x })])));
  $("kept").replaceChildren(...d.kept.map((x) => el("li", { textContent: x })));
  $("never").replaceChildren(...d.never.map((x) => el("li", { textContent: x })));
  const open = [...$("faqList").querySelectorAll("details")].map((x) => x.open);
  $("faqList").replaceChildren(...d.faq.map(([q, a], i) => {
    const det = el("details", {}, [el("summary", { textContent: titleCase(q) }), el("p", { textContent: a })]);
    det.open = open.length ? open[i] : i === 0;
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
  document.querySelectorAll("[data-i18n]").forEach((n) => { n.textContent = d[n.dataset.i18n]; });
  document.querySelectorAll("[data-tc]").forEach((n) => { const v = d[n.dataset.tc]; n.textContent = VERBATIM.has(n.dataset.tc) ? v : titleCase(v); });
  document.querySelectorAll("[data-i18n-aria]").forEach((n) => n.setAttribute("aria-label", d[n.dataset.i18nAria]));
  $("heroImg").alt = d.heroAlt;
  $("langId").setAttribute("aria-pressed", String(lang === "id"));
  $("langEn").setAttribute("aria-pressed", String(lang === "en"));
  const cb = $("copyBtn");
  if (!cb.dataset.state) cb.textContent = titleCase(d.copy);
  renderLists();
}

function applyTheme() {
  document.documentElement.dataset.theme = theme;
  const bg = theme === "dark" ? "#000000" : "#EEF2F8";
  document.querySelectorAll('meta[name="theme-color"]').forEach((m) => { m.content = bg; });
  // gambar hero mengikuti tema pilihan (bukan hanya pengaturan sistem); ukurannya sama, jadi tidak ada pergeseran tata letak
  $("heroDark").media = theme === "dark" ? "all" : "not all";
  // ikon bulan saat tema terang aktif, matahari saat gelap, seperti di panel
  $("themeIcon").innerHTML = theme === "dark"
    ? '<circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6L7 7M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4"/>'
    : '<path d="M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z"/>';
}

function remember() { store.set(LANG_KEY, lang); store.set(THEME_KEY, theme); }
$("langId").addEventListener("click", () => { lang = "id"; store.set(LANG_KEY, lang); applyText(); });
$("langEn").addEventListener("click", () => { lang = "en"; store.set(LANG_KEY, lang); applyText(); });
$("themeBtn").addEventListener("click", () => { theme = theme === "dark" ? "light" : "dark"; store.set(THEME_KEY, theme); applyTheme(); });
// pilihan bahasa dan tema ikut ke halaman login walau belum pernah diubah manual
document.querySelectorAll("[data-login]").forEach((a) => a.addEventListener("click", remember));

// tautan panduan hanya tampil bila LANDING_DOCS_URL diisi
const docs = $("docsBtn");
const docsUrl = docs.dataset.docs || "";
if (/^https?:\/\//i.test(docsUrl)) { docs.href = docsUrl; $("docsRow").classList.remove("hidden"); }

// salin perintah pasang: Clipboard API, lalu execCommand, lalu teks dipilih agar bisa disalin manual
function selectCmd() {
  const r = document.createRange();
  r.selectNodeContents($("cmd"));
  const s = getSelection();
  s.removeAllRanges();
  s.addRange(r);
}
let copyTimer = null;
function copyDone(ok) {
  const d = DICT[lang], btn = $("copyBtn"), msg = $("copyMsg");
  msg.classList.toggle("err", !ok);
  msg.textContent = ok ? d.copyOk : d.copyFail;
  clearTimeout(copyTimer);
  if (ok) {
    btn.dataset.state = "copied";
    btn.textContent = titleCase(d.copied);
    copyTimer = setTimeout(() => { delete btn.dataset.state; btn.textContent = titleCase(DICT[lang].copy); msg.textContent = ""; }, 2500);
  }
}
$("copyBtn").addEventListener("click", async () => {
  const text = $("cmd").textContent;
  try {
    if (!(navigator.clipboard && navigator.clipboard.writeText)) throw new Error("no clipboard");
    await navigator.clipboard.writeText(text);
    copyDone(true);
  } catch (e) {
    selectCmd();
    let ok = false;
    try { ok = !!(document.execCommand && document.execCommand("copy")); } catch (e2) { ok = false; }
    copyDone(ok);
  }
});

// scroll halus ke bagian halaman (menghormati prefers-reduced-motion); tautan lama (bahasa Indonesia) dipetakan ke ID baru
const reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)");
const OLD_HASH = { features: "how-it-works", fitur: "how-it-works", cara: "how-it-works", aman: "security" };
function goTo(id, smooth) {
  id = OLD_HASH[id] || id;
  const target = id && $(id);
  if (!target) return false;
  target.scrollIntoView({ behavior: smooth && !(reduce && reduce.matches) ? "smooth" : "auto", block: "start" });
  if (location.hash !== "#" + id) history.replaceState(null, "", "#" + id);
  if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
  target.focus({ preventScroll: true });
  return true;
}
document.querySelectorAll('a[href^="#"]').forEach((a) => a.addEventListener("click", (e) => {
  if (goTo(a.getAttribute("href").slice(1), true)) e.preventDefault();
}));
window.addEventListener("hashchange", () => { goTo(location.hash.slice(1), true); });

applyTheme();
applyText();
if (location.hash.length > 1) goTo(location.hash.slice(1), false);
window.__landingReady = true;
})();
