(() => {
  const $ = (id) => document.getElementById(id);
  const NS = "http://www.w3.org/2000/svg";
  const KEY = "streak_panel_key";
  const ACCT_KEY = "streak_panel_account";
  const LANG_KEY = "streak_panel_lang";
  const THEME_KEY = "streak_panel_theme";

  // ------------------------------------------------------------------ i18n
  // Semua teks UI memakai Title Case (konektor selain kata pertama tetap huruf kecil)
  const I18N = {
    id: {
      brand: "Streak Panel", loginHint: "Masukkan Kunci Akses untuk Membuka Panel", accessKey: "Kunci Akses", signIn: "Masuk",
      wrongKey: "Kunci Akses Salah", navLabel: "Navigasi Utama", navDashboard: "Dashboard", navAccounts: "Akun & Jadwal",
      navContacts: "Kontak", navCookies: "Cookie & Login", navSettings: "Pengaturan", language: "Bahasa", toggleTheme: "Ganti Tema",
      activeAccount: "Akun Aktif", signOut: "Keluar", nextSchedule: "Jadwal Berikutnya", customMessagePh: "Pesan Khusus (Opsional)",
      sendNow: "Kirim Sekarang", dryRun: "Uji Tanpa Kirim", stop: "Hentikan", streakDays: "Hari Beruntun", todayGoal: "Target Hari Ini",
      last7Days: "7 Hari Terakhir", cookie: "Cookie", cookieRefresh: "Penyegaran Cookie", notifications: "Notifikasi", accounts: "Akun",
      today: "Hari Ini", latestLog: "Log Terbaru", viewScreenshot: "Lihat Tangkapan Layar", history: "Riwayat", clearHistory: "Hapus Riwayat",
      colTime: "Waktu", colAccount: "Akun", colType: "Jenis", colResult: "Hasil", colDuration: "Durasi", colStatus: "Status",
      accountsHint: "Kelola Akun TikTok dan Jadwal Kirim", newAccountName: "Nama Akun Baru", newAccountPh: "Contoh: Akun Kedua",
      addAccount: "Tambah Akun", sendSchedules: "Jadwal Kirim", schedulesHint: "Atur Jam, Pesan, dan Penerima untuk Setiap Jadwal",
      schedulesSaveHint: "Tekan Simpan Jadwal untuk Menerapkan Perubahan", saveSchedules: "Simpan Jadwal", addSchedule: "Tambah Jadwal",
      contactsHint: "Kontak yang Menerima Pesan Streak", addContacts: "Tambah Kontak", contactsPh: "Satu Nama per Baris, Persis seperti di Daftar Pesan TikTok",
      add: "Tambah", contactList: "Daftar Kontak", account: "Akun", checkCookieNow: "Cek Cookie Sekarang", reLogin: "Login Ulang",
      idleNote: "Browser Server", remoteHint: "Buka Browser di Server, lalu Login ke TikTok dari Sini", startLogin: "Buka Browser Login",
      remoteBrowser: "Tampilan Browser Server", sendText: "Kirim Teks", sendTextPh: "Ketik lalu Tekan Enter",
      tip1: "Klik pada Layar untuk Memilih Kolom", tip2: "Gunakan Kolom Teks untuk Menempel Kata Sandi", tip3: "Setelah Login Terdeteksi, Simpan Sesi Login",
      saveLoginSession: "Simpan Sesi Login", cancel: "Batal", manualCookie: "Tempel Cookie Manual", manualCookieHint: "Alternatif Jika Login lewat Browser Server Gagal",
      cookiePh: "Tempel Cookie di Sini (JSON atau Header)", saveCookie: "Simpan Cookie", deleteCookie: "Hapus Cookie",
      settingsHint: "Atur Pesan, Cookie, dan Notifikasi", message: "Pesan", defaultMessage: "Pesan Default", timezone: "Zona Waktu",
      keepalive: "Segarkan Cookie Otomatis", keepaliveHours: "Interval Penyegaran (Jam)", waits: "Waktu Tunggu (Detik)", pageLoad: "Muat Halaman",
      element: "Elemen", sendDelay: "Jeda Antar Kirim", proof: "Bukti", attachScreenshot: "Lampirkan Tangkapan Layar",
      attachScreenshotHint: "Kirim Tangkapan Layar Chat bersama Notifikasi", enableNotif: "Aktifkan Notifikasi", webhookUrl: "URL Webhook",
      testDiscord: "Kirim Pesan Uji Discord", botToken: "Token Bot", keepEmptyPh: "Kosongkan untuk Mempertahankan", chatId: "ID Chat",
      testTelegram: "Kirim Pesan Uji Telegram", save: "Simpan",
      // dari JS
      saved: "(Tersimpan)", ready: "Siap", busyAcct: "Berjalan: {name}", busy: "Berjalan",
      st_running: "Berjalan", st_success: "Berhasil", st_partial: "Sebagian", st_failed: "Gagal", st_cancelled: "Dihentikan",
      st_missed: "Terlewat", st_pending: "Menunggu",
      noSchedule: "Belum Ada Jadwal Aktif", noScheduleHint: "Tambahkan Jadwal di Tab Akun & Jadwal",
      allContacts: "Semua Kontak ({n})", nContacts: "{n} Kontak", nContacts1: "{n} Kontak",
      partMorning: "Pagi", partNoon: "Siang", partAfternoon: "Sore", partNight: "Malam",
      ringAria: "Sisa Waktu ke Jadwal Berikutnya: {time}", ringNone: "Tidak Ada Jadwal Berikutnya",
      cookieValid: "Valid", cookieInvalid: "Tidak Valid", cookieUnset: "Belum Diatur",
      checkedAgo: "Dicek {when}", notVerified: "Belum Diverifikasi", savedAgo: "Disimpan {when}",
      refreshEvery: "Setiap {n} Jam", refreshEvery1: "Setiap {n} Jam", refreshOff: "Nonaktif",
      refreshOn: "Menjaga Sesi Tetap Aktif", refreshOffSub: "Cookie Bisa Kedaluwarsa",
      notifOff: "Nonaktif", notifShot: "Dengan Tangkapan Layar", notifNoShot: "Tanpa Tangkapan Layar", notifNone: "Belum Ada Notifikasi",
      nAccounts: "{n} Akun", nAccounts1: "{n} Akun", totalContacts: "Total {n} Kontak",
      nSchedules: "{n} Jadwal", nSchedules1: "{n} Jadwal", emptyToday: "Belum Ada Jadwal Aktif Hari Ini",
      noHistory: "Belum Ada Riwayat", noContacts: "Belum Ada Kontak", noContactsHere: "Belum Ada Kontak di Akun Ini", noScheds: "Belum Ada Jadwal",
      typeSend: "Kirim", typeTest: "Uji", typeCheck: "Cek Cookie", trManual: "Manual", trAuto: "Otomatis",
      clickForLog: "Klik untuk Melihat Log", durMin: "{m} Mnt {s} Dtk", durSec: "{s} Dtk",
      confirmSend: "Kirim Pesan Streak ke Semua Kontak Akun {name} Sekarang?", confirmClear: "Hapus Semua Riwayat?",
      confirmDeleteAccount: "Hapus Akun \"{name}\" beserta Cookie, Kontak, dan Jadwalnya?", confirmClearCookies: "Hapus Cookie Tersimpan?",
      promptAccountName: "Nama Akun:", promptRename: "Nama Baru untuk Kontak Ini (Persis seperti di Daftar Pesan TikTok):",
      toastStopping: "Menghentikan…", toastChecking: "Mengecek Cookie… Lihat Log di Dashboard", toastCookieSaved: "Cookie Disimpan",
      toastLoginSaved: "Login Tersimpan", toastSchedulesSaved: "Jadwal Disimpan", toastSettingsSaved: "Pengaturan Disimpan",
      toastTestSent: "Pesan Uji Terkirim", toastAdded: "{n} Kontak Ditambahkan", toastAccountCreated: "Akun \"{name}\" Dibuat. Atur Cookie di Tab Cookie",
      maxSchedules: "Maksimal 8 Jadwal",
      pick: "Pilih", picked: "Dipilih", rename: "Ubah Nama", del: "Hapus", renameAria: "Ubah Nama {name}", delAria: "Hapus {name}",
      acctMeta: "{contacts} · {cookie} · Berikutnya {next}", cookieBriefOk: "Cookie OK", cookieBriefSaved: "Cookie Tersimpan",
      cookieBriefBad: "Cookie Tidak Valid", cookieBriefNone: "Cookie Belum Diatur", noNext: "Tidak Ada",
      schedEnabled: "Jadwal Aktif", schedMsgPh: "Pesan Khusus (Kosong = Default)", sendToAll: "Kirim ke Semua Kontak", hour: "Jam", minute: "Menit",
      delSched: "Hapus Jadwal {time}", tzLabel: "Zona Waktu: {tz}", tzServer: "Server",
      bannerOk: "Cookie Valid", bannerBad: "Cookie Tidak Valid", bannerNone: "Belum Ada Cookie", bannerNoneSub: "Login atau Tempel Cookie untuk Memulai",
      cookieCount: "{n} Cookie", warnNoSession: "Peringatan: Sessionid Tidak Ditemukan",
      step1: "Buka Browser", step2: "Login ke TikTok", step3: "Simpan Sesi",
      loginOpening: "Membuka Browser…", loginWaiting: "Menunggu Login…", loginDetected: "Login Terdeteksi. Klik Simpan Sesi Login",
      loginEnded: "Sesi Login Berakhir", loginCancelled: "Dibatalkan", loginSaved: "Berhasil: {n} Cookie Tersimpan",
      proofAlt: "Bukti {name}", evChat: "Chat Terverifikasi", evBubble: "Bubble Terverifikasi", evList: "Daftar Chat {time}",
      evRenamed: "Nama Baru {name}, Diperbarui Otomatis",
      rtNow: "Baru Saja", dash: "-",
      noRuns: "Belum Ada Proses", lbClose: "Tutup", lbDownload: "Unduh", lbPrev: "Sebelumnya", lbNext: "Berikutnya",
      lbLatestShot: "Tangkapan Layar Terakhir", lbZoomIn: "Klik untuk Ukuran Asli", lbZoomOut: "Klik untuk Muat Layar", lbViewer: "Penampil Gambar",
    },
    en: {
      brand: "Streak Panel", loginHint: "Enter Your Access Key to Open the Panel", accessKey: "Access Key", signIn: "Log In",
      wrongKey: "Wrong Access Key", navLabel: "Main Navigation", navDashboard: "Dashboard", navAccounts: "Accounts & Schedules",
      navContacts: "Contacts", navCookies: "Cookie & Login", navSettings: "Settings", language: "Language", toggleTheme: "Toggle Theme",
      activeAccount: "Active Account", signOut: "Sign Out", nextSchedule: "Next Schedule", customMessagePh: "Custom Message (Optional)",
      sendNow: "Send Now", dryRun: "Test Without Sending", stop: "Stop", streakDays: "Day Streak", todayGoal: "Today's Goal",
      last7Days: "Last 7 Days", cookie: "Cookie", cookieRefresh: "Cookie Refresh", notifications: "Notifications", accounts: "Accounts",
      today: "Today", latestLog: "Latest Log", viewScreenshot: "View Screenshot", history: "History", clearHistory: "Clear History",
      colTime: "Time", colAccount: "Account", colType: "Type", colResult: "Result", colDuration: "Duration", colStatus: "Status",
      accountsHint: "Manage TikTok Accounts and Send Schedules", newAccountName: "New Account Name", newAccountPh: "Example: Second Account",
      addAccount: "Add Account", sendSchedules: "Send Schedules", schedulesHint: "Set the Time, Message, and Recipients for Each Schedule",
      schedulesSaveHint: "Press Save Schedules to Apply Changes", saveSchedules: "Save Schedules", addSchedule: "Add Schedule",
      contactsHint: "Contacts That Receive Streak Messages", addContacts: "Add Contacts", contactsPh: "One Name per Line, Exactly as in the TikTok Message List",
      add: "Add", contactList: "Contact List", account: "Account", checkCookieNow: "Check Cookie Now", reLogin: "Log In Again",
      idleNote: "Server Browser", remoteHint: "Open a Browser on the Server, Then Log In to TikTok from Here", startLogin: "Open Login Browser",
      remoteBrowser: "Server Browser View", sendText: "Send Text", sendTextPh: "Type Then Press Enter",
      tip1: "Click on the Screen to Select a Field", tip2: "Use the Text Field to Paste Passwords", tip3: "Once Login Is Detected, Save the Login Session",
      saveLoginSession: "Save Login Session", cancel: "Cancel", manualCookie: "Paste Cookie Manually", manualCookieHint: "Alternative if Login via Server Browser Fails",
      cookiePh: "Paste Cookie Here (JSON or Header)", saveCookie: "Save Cookie", deleteCookie: "Delete Cookie",
      settingsHint: "Configure Messages, Cookies, and Notifications", message: "Message", defaultMessage: "Default Message", timezone: "Time Zone",
      keepalive: "Refresh Cookie Automatically", keepaliveHours: "Refresh Interval (Hours)", waits: "Wait Times (Seconds)", pageLoad: "Page Load",
      element: "Element", sendDelay: "Delay Between Sends", proof: "Proof", attachScreenshot: "Attach Screenshot",
      attachScreenshotHint: "Send a Chat Screenshot with the Notification", enableNotif: "Enable Notifications", webhookUrl: "Webhook URL",
      testDiscord: "Send Discord Test Message", botToken: "Bot Token", keepEmptyPh: "Leave Empty to Keep", chatId: "Chat ID",
      testTelegram: "Send Telegram Test Message", save: "Save",
      saved: "(Saved)", ready: "Ready", busyAcct: "Running: {name}", busy: "Running",
      st_running: "Running", st_success: "Success", st_partial: "Partial", st_failed: "Failed", st_cancelled: "Stopped",
      st_missed: "Missed", st_pending: "Pending",
      noSchedule: "No Active Schedule", noScheduleHint: "Add One in the Accounts & Schedules Tab",
      allContacts: "All Contacts ({n})", nContacts: "{n} Contacts", nContacts1: "{n} Contact",
      partMorning: "Morning", partNoon: "Noon", partAfternoon: "Afternoon", partNight: "Night",
      ringAria: "Time Left to Next Schedule: {time}", ringNone: "No Next Schedule",
      cookieValid: "Valid", cookieInvalid: "Invalid", cookieUnset: "Not Set",
      checkedAgo: "Checked {when}", notVerified: "Not Verified Yet", savedAgo: "Saved {when}",
      refreshEvery: "Every {n} Hours", refreshEvery1: "Every {n} Hour", refreshOff: "Off",
      refreshOn: "Keeps the Session Alive", refreshOffSub: "Cookie May Expire",
      notifOff: "Off", notifShot: "With Screenshots", notifNoShot: "Without Screenshots", notifNone: "No Notifications Yet",
      nAccounts: "{n} Accounts", nAccounts1: "{n} Account", totalContacts: "{n} Contacts in Total",
      nSchedules: "{n} Schedules", nSchedules1: "{n} Schedule", emptyToday: "No Active Schedules Today",
      noHistory: "No History Yet", noContacts: "No Contacts Yet", noContactsHere: "No Contacts in This Account", noScheds: "No Schedules Yet",
      typeSend: "Send", typeTest: "Test", typeCheck: "Cookie Check", trManual: "Manual", trAuto: "Automatic",
      clickForLog: "Click to View Log", durMin: "{m}m {s}s", durSec: "{s}s",
      confirmSend: "Send Streak Message to All Contacts of {name} Now?", confirmClear: "Delete All History?",
      confirmDeleteAccount: "Delete Account \"{name}\" with Its Cookies, Contacts, and Schedules?", confirmClearCookies: "Delete Saved Cookie?",
      promptAccountName: "Account Name:", promptRename: "New Name for This Contact (Exactly as in the TikTok Message List):",
      toastStopping: "Stopping…", toastChecking: "Checking Cookie… See the Log on the Dashboard", toastCookieSaved: "Cookie Saved",
      toastLoginSaved: "Login Saved", toastSchedulesSaved: "Schedules Saved", toastSettingsSaved: "Settings Saved",
      toastTestSent: "Test Message Sent", toastAdded: "{n} Contacts Added", toastAccountCreated: "Account \"{name}\" Created. Set Its Cookie in the Cookies Tab",
      maxSchedules: "Maximum 8 Schedules",
      pick: "Select", picked: "Selected", rename: "Rename", del: "Delete", renameAria: "Rename {name}", delAria: "Delete {name}",
      acctMeta: "{contacts} · {cookie} · Next {next}", cookieBriefOk: "Cookie OK", cookieBriefSaved: "Cookie Saved",
      cookieBriefBad: "Cookie Invalid", cookieBriefNone: "Cookie Not Set", noNext: "None",
      schedEnabled: "Schedule Enabled", schedMsgPh: "Custom Message (Empty = Default)", sendToAll: "Send to All Contacts", hour: "Hour", minute: "Minute",
      delSched: "Delete Schedule {time}", tzLabel: "Time Zone: {tz}", tzServer: "Server",
      bannerOk: "Cookie Valid", bannerBad: "Cookie Invalid", bannerNone: "No Cookie Yet", bannerNoneSub: "Log In or Paste a Cookie to Start",
      cookieCount: "{n} Cookies", warnNoSession: "Warning: Sessionid Not Found",
      step1: "Open Browser", step2: "Log In to TikTok", step3: "Save Session",
      loginOpening: "Opening Browser…", loginWaiting: "Waiting for Login…", loginDetected: "Login Detected. Click Save Login Session",
      loginEnded: "Login Session Ended", loginCancelled: "Cancelled", loginSaved: "Success: {n} Cookies Saved",
      proofAlt: "Proof {name}", evChat: "Chat Verified", evBubble: "Bubble Verified", evList: "Chat List {time}",
      evRenamed: "New Name {name}, Updated Automatically",
      rtNow: "Just Now", dash: "-",
      noRuns: "No Runs Yet", lbClose: "Close", lbDownload: "Download", lbPrev: "Previous", lbNext: "Next",
      lbLatestShot: "Latest Screenshot", lbZoomIn: "Click for Actual Size", lbZoomOut: "Click to Fit Screen", lbViewer: "Image Viewer",
    },
  };
  const CONNECTORS = {
    id: new Set(["di", "ke", "dari", "dan", "atau", "yang", "untuk", "dengan", "pada", "per"]),
    en: new Set(["a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "at", "by", "with"]),
  };
  const LOCALE = { id: "id-ID", en: "en-US" };

  let lang = "id";
  let theme = "light";
  let apiKey = "";
  let currentId = "";
  try {
    apiKey = localStorage.getItem(KEY) || "";
    currentId = localStorage.getItem(ACCT_KEY) || "";
    const l = localStorage.getItem(LANG_KEY);
    if (l === "id" || l === "en") lang = l;
  } catch (e) { /* storage tidak tersedia */ }

  function titleCase(s) {
    return String(s).split(/(\s+)/).map((w, i) => {
      if (!w.trim() || w.includes("{")) return w;
      if (i > 0 && CONNECTORS[lang].has(w.toLowerCase())) return w.toLowerCase();
      return w.replace(/\p{L}/u, (c) => c.toUpperCase());
    }).join("");
  }

  // Terjemahan + Title Case, lalu isi placeholder {x}
  function t(key, vars) {
    const raw = I18N[lang][key] ?? I18N.id[key] ?? key;
    let s = titleCase(raw);
    if (vars) s = s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? vars[k] : m));
    return s;
  }
  // Bentuk jamak/tunggal: key1 dipakai bila n == 1
  const tn = (key, n) => t(n === 1 && I18N[lang][key + "1"] ? key + "1" : key, { n });

  // ------------------------------------------------------------------ state
  let accounts = [];
  let serverNow = "";
  let st = null;            // /api/status terakhir
  let settings = null;
  let history = [];
  let contactList = [];
  let logCursor = 0;
  let lastRunId = null;
  let pinned = false;       // true saat melihat log dari riwayat
  let pollTimer = null;
  let histTimer = null;
  let wasRunning = false;
  let dashSig = "";
  let loginTimer = null;
  let framePending = false;
  let loginMode = "idle";   // idle | open | logged
  let loginMsg = null;      // {key, vars, raw, cls}

  // ---------------------------------------------------------------- helpers
  async function api(path, opts = {}) {
    const res = await fetch("/api" + path, {
      method: opts.method || "GET",
      headers: { "X-API-Key": apiKey, ...(opts.body ? { "Content-Type": "application/json" } : {}) },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    if (res.status === 401) { showLogin(); throw new Error("Unauthorized"); }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  }
  const apiA = (path, opts) => api(path + (path.includes("?") ? "&" : "?") + "account=" + encodeURIComponent(currentId), opts);
  const curAccount = () => accounts.find((a) => a.id === currentId) || accounts[0];

  function el(tag, props = {}, children = []) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
      if (k.includes("-") || k === "role") n.setAttribute(k, v);
      else n[k] = v;
    }
    children.forEach((c) => n.append(c));
    return n;
  }
  function icon(id, cls) {
    const s = document.createElementNS(NS, "svg");
    s.setAttribute("aria-hidden", "true");
    if (cls) s.setAttribute("class", cls);
    const u = document.createElementNS(NS, "use");
    u.setAttribute("href", "#" + id);
    s.append(u);
    return s;
  }
  const setText = (id, text) => { $(id).textContent = text; };
  const pad = (n) => String(n).padStart(2, "0");
  const clamp = (n, a, b) => Math.min(b, Math.max(a, n));

  function toast(msg) {
    const e = $("toast");
    e.textContent = msg;
    e.classList.remove("hidden");
    clearTimeout(toast.t);
    toast.t = setTimeout(() => e.classList.add("hidden"), 2500);
  }

  // Pesan yang bisa berupa teks terjemahan (hint) atau error dari server
  function setMsg(id, text, hintKey) {
    const e = $(id);
    if (text) { e.removeAttribute("data-i18n"); e.textContent = text; }
    else if (hintKey) { e.setAttribute("data-i18n", hintKey); e.textContent = t(hintKey); }
    else e.textContent = "";
  }

  // Waktu server bersifat naive (tanpa zona), jadi semua selisih dihitung antar string server
  const parseNaive = (iso) => new Date(iso);
  const dayOf = (iso) => (iso || "").slice(0, 10);
  const hhmmOf = (iso) => (iso || "").slice(11, 16);
  function addDays(day, n) {
    const d = new Date(day + "T12:00:00Z");
    d.setUTCDate(d.getUTCDate() + n);
    return d.toISOString().slice(0, 10);
  }
  const dayDate = (day) => new Date(day + "T12:00:00Z");

  function relTime(iso) {
    if (!iso || !serverNow) return "";
    const sec = Math.round((parseNaive(serverNow) - parseNaive(iso)) / 1000);
    const rtf = new Intl.RelativeTimeFormat(LOCALE[lang], { numeric: "auto" });
    let s;
    if (sec < 45) s = t("rtNow");
    else if (sec < 3600) s = rtf.format(-Math.round(sec / 60), "minute");
    else if (sec < 86400) s = rtf.format(-Math.round(sec / 3600), "hour");
    else s = rtf.format(-Math.round(sec / 86400), "day");
    return titleCase(s);
  }

  function fmtDateTime(iso) {
    if (!iso) return "-";
    const d = new Intl.DateTimeFormat(LOCALE[lang], { day: "numeric", month: "short", timeZone: "UTC" }).format(dayDate(dayOf(iso)));
    return titleCase(`${d} ${hhmmOf(iso)}`);
  }

  function duration(r) {
    if (!r.started_at || !r.finished_at) return "-";
    const sec = Math.max(0, Math.round((parseNaive(r.finished_at) - parseNaive(r.started_at)) / 1000));
    return sec >= 60 ? t("durMin", { m: Math.floor(sec / 60), s: pad(sec % 60) }) : t("durSec", { s: sec });
  }

  const partKey = (h) => (h < 11 ? "partMorning" : h < 15 ? "partNoon" : h < 18 ? "partAfternoon" : "partNight");
  const partName = (h) => t(partKey(h));
  const slotPart = (time) => partName(parseInt(time.slice(0, 2), 10));

  function badge(status, label) {
    return el("span", { className: "badge " + status, textContent: label || t("st_" + status) });
  }
  const statusLabel = (s) => (I18N.id["st_" + s] ? t("st_" + s) : s);

  // ------------------------------------------------------------- theme / lang
  function applyTheme(th) {
    theme = th;
    document.documentElement.dataset.theme = th;
    const m = document.querySelector('meta[name="theme-color"]');
    if (m) m.content = th === "dark" ? "#000000" : "#EEF2F8";
  }
  let initialTheme = "light";
  try {
    initialTheme = localStorage.getItem(THEME_KEY) || (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  } catch (e) { /* abaikan */ }
  applyTheme(initialTheme === "dark" ? "dark" : "light");
  $("themeBtn").addEventListener("click", () => {
    applyTheme(theme === "dark" ? "light" : "dark");
    try { localStorage.setItem(THEME_KEY, theme); } catch (e) { /* abaikan */ }
  });

  const TAB_KEYS = { dashboard: "navDashboard", accounts: "navAccounts", contacts: "navContacts", cookies: "navCookies", settings: "navSettings" };
  function applyStaticI18n() {
    document.querySelectorAll("#tabs [data-tab]").forEach((b) => {
      const label = t(TAB_KEYS[b.dataset.tab]);
      b.setAttribute("aria-label", label);
      b.title = label;
    });
    const map = { i18n: (n, v) => { n.textContent = v; }, "i18n-ph": (n, v) => { n.placeholder = v; },
      "i18n-aria": (n, v) => n.setAttribute("aria-label", v), "i18n-title": (n, v) => { n.title = v; },
      "i18n-alt": (n, v) => { n.alt = v; } };
    for (const [attr, fn] of Object.entries(map)) {
      document.querySelectorAll(`[data-${attr}]`).forEach((n) => fn(n, t(n.getAttribute("data-" + attr))));
    }
  }

  function setLang(l) {
    lang = l;
    try { localStorage.setItem(LANG_KEY, l); } catch (e) { /* abaikan */ }
    document.documentElement.lang = l;
    document.querySelectorAll(".segmented [data-lang]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === l)));
    applyStaticI18n();
    renderAll();
  }
  document.querySelectorAll(".segmented [data-lang]").forEach((b) => b.addEventListener("click", () => setLang(b.dataset.lang)));

  // ------------------------------------------------------------------- auth
  function showLogin() {
    $("app").classList.add("hidden");
    $("login").classList.remove("hidden");
    clearInterval(pollTimer);
    clearInterval(histTimer);
  }

  async function enter() {
    st = await api("/status");
    serverNow = st.server_now || serverNow;
    syncAccounts(st.accounts);
    $("login").classList.add("hidden");
    $("app").classList.remove("hidden");
    await Promise.all([loadSettings(), loadContacts(), loadHistory()]);
    renderSchedules(curAccount().schedules);
    await refresh();
    clearInterval(pollTimer);
    clearInterval(histTimer);
    pollTimer = setInterval(refresh, 2000);
    histTimer = setInterval(() => loadHistory().catch(() => {}), 30000);
  }

  $("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    apiKey = $("keyInput").value.trim();
    $("loginErr").textContent = "";
    try {
      await enter();
      try { localStorage.setItem(KEY, apiKey); } catch (err) { /* abaikan */ }
    } catch (err) {
      $("loginErr").textContent = err.message === "Unauthorized" || /HTTP 401/.test(err.message) ? t("wrongKey") : err.message;
      showLogin();
    }
  });

  $("logout").addEventListener("click", () => {
    try { localStorage.removeItem(KEY); } catch (e) { /* abaikan */ }
    apiKey = "";
    $("keyInput").value = "";
    showLogin();
  });

  // ------------------------------------------------------------------- tabs
  function showTab(tab) {
    document.querySelectorAll("#tabs button").forEach((b) => {
      const on = b.dataset.tab === tab;
      b.classList.toggle("active", on);
      if (on) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
    });
    document.querySelectorAll("main > section").forEach((s) => s.classList.toggle("hidden", s.id !== "tab-" + tab));
    window.scrollTo({ top: 0 });
  }
  $("tabs").addEventListener("click", (e) => {
    const b = e.target.closest("[data-tab]");
    if (b) showTab(b.dataset.tab);
  });
  document.querySelectorAll("[data-goto]").forEach((a) => a.addEventListener("click", (e) => {
    e.preventDefault();
    showTab(a.dataset.goto);
  }));

  // ---------------------------------------------------------------- accounts
  // Sinkronkan daftar akun dari server; return true bila akun terpilih berubah
  function syncAccounts(list) {
    accounts = list;
    let changed = false;
    if (!accounts.find((a) => a.id === currentId)) {
      currentId = accounts[0].id;
      changed = true;
      try { localStorage.setItem(ACCT_KEY, currentId); } catch (e) { /* abaikan */ }
    }
    const sig = JSON.stringify(accounts.map((a) => [a.id, a.name, a.cookies.invalid ? 1 : 0]));
    const sel = $("accountSelect");
    if (sel.dataset.sig !== sig) {
      sel.dataset.sig = sig;
      sel.replaceChildren(...accounts.map((a) => new Option(a.name + (a.cookies.invalid ? " (!)" : ""), a.id)));
    }
    sel.value = currentId;
    const name = curAccount().name;
    $("acctAvatar").textContent = (name.trim()[0] || "?").toUpperCase();
    document.querySelectorAll(".acct-name-text").forEach((n) => { n.textContent = name; });
    renderAccountList();
    return changed;
  }

  async function switchAccount(id) {
    currentId = id;
    try { localStorage.setItem(ACCT_KEY, id); } catch (e) { /* abaikan */ }
    if (loginTimer || loginMode !== "idle") { await api("/login/stop", { method: "POST" }).catch(() => {}); endLogin(null); }
    syncAccounts(accounts);
    dashSig = "";
    await loadContacts();
    renderSchedules(curAccount().schedules);
    await refresh();
  }
  $("accountSelect").addEventListener("change", (e) => switchAccount(e.target.value));

  function cookieBrief(c) {
    return t(c.invalid ? "cookieBriefBad" : !c.present ? "cookieBriefNone" : c.last_ok ? "cookieBriefOk" : "cookieBriefSaved");
  }

  function renderAccountList(force) {
    const sig = JSON.stringify([lang, currentId, accounts]);
    if (!force && renderAccountList.sig === sig) return;
    renderAccountList.sig = sig;
    const box = $("accountList");
    box.replaceChildren();
    accounts.forEach((a) => {
      const on = a.id === currentId;
      const pick = el("button", { className: "btn plain small", type: "button", textContent: on ? t("picked") : t("pick"), disabled: on });
      const ren = el("button", { className: "btn plain small", type: "button", textContent: t("rename"), "aria-label": t("renameAria", { name: a.name }) });
      const del = el("button", { className: "btn plain small destructive-text", type: "button", textContent: t("del"), disabled: accounts.length < 2, "aria-label": t("delAria", { name: a.name }) });
      pick.addEventListener("click", () => switchAccount(a.id));
      ren.addEventListener("click", async () => {
        const name = prompt(t("promptAccountName"), a.name);
        if (!name || name.trim() === a.name) return;
        try { await api("/accounts/" + a.id, { method: "PUT", body: { name } }); await refresh(); }
        catch (e) { toast(e.message); }
      });
      del.addEventListener("click", async () => {
        if (!confirm(t("confirmDeleteAccount", { name: a.name }))) return;
        try { await api("/accounts/" + a.id, { method: "DELETE" }); await refresh(); }
        catch (e) { toast(e.message); }
      });
      const meta = t("acctMeta", { contacts: tn("nContacts", a.contacts), cookie: cookieBrief(a.cookies), next: a.next ? a.next.time : t("noNext") });
      box.append(el("div", { className: on ? "current" : "" }, [
        el("span", { className: "avatar-sm" + (on ? " on" : ""), textContent: (a.name.trim()[0] || "?").toUpperCase(), "aria-hidden": "true" }),
        el("div", { className: "grow" }, [el("div", { className: "title", textContent: a.name }), el("div", { className: "meta", textContent: meta })]),
        el("div", { className: "actions" }, [pick, ren, del]),
      ]));
    });
  }

  $("btnAddAccount").addEventListener("click", async () => {
    $("accountErr").textContent = "";
    try {
      const acc = await api("/accounts", { method: "POST", body: { name: $("newAccountName").value } });
      $("newAccountName").value = "";
      st = await api("/status");
      serverNow = st.server_now || serverNow;
      syncAccounts(st.accounts);
      await switchAccount(acc.id);
      toast(t("toastAccountCreated", { name: acc.name }));
    } catch (e) { $("accountErr").textContent = e.message; }
  });

  // -------------------------------------------------------------- dashboard
  const slotsOfToday = (a) => a.schedules.filter((s) => s.enabled).sort((x, y) => x.time.localeCompare(y.time));
  const expectedCount = (a, s) => (s.contacts == null ? a.contacts : s.contacts.length);
  const recipText = (a, contacts) => (contacts == null ? t("allContacts", { n: a.contacts }) : tn("nContacts", contacts.length));

  function ringState(a) {
    const n = a.next;
    const fg = $("ringFg");
    if (!n) {
      fg.setAttribute("stroke-dashoffset", "377");
      setText("ringText", "--");
      $("ringSvg").setAttribute("aria-label", t("ringNone"));
      return;
    }
    const rem = Math.max(0, n.epoch - Date.now() / 1000);
    const progress = clamp(1 - rem / 86400, 0, 1);
    fg.setAttribute("stroke-dashoffset", String(377 * (1 - progress)));
    const txt = `${Math.floor(rem / 3600)}:${pad(Math.floor((rem % 3600) / 60))}`;
    setText("ringText", txt);
    $("ringSvg").setAttribute("aria-label", t("ringAria", { time: txt }));
  }

  function renderDashboard(force) {
    if (!st || !accounts.length) return;
    const a = curAccount();
    ringState(a);
    const sig = JSON.stringify([lang, currentId, accounts, st.running, st.current && [st.current.id, st.current.status, st.current.sent, (st.current.results || []).length],
      serverNow.slice(0, 16), history.map((r) => [r.id, r.status, r.sent]), settings, contactList]);
    if (!force && sig === dashSig) return;
    dashSig = sig;

    const today = dayOf(serverNow);
    const nowHm = hhmmOf(serverNow);
    setText("dashDate", titleCase(new Intl.DateTimeFormat(LOCALE[lang], { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" }).format(dayDate(today))));

    // pil antrean
    const pill = $("queuePill");
    pill.className = "pill " + (st.running ? "busy" : "ok");
    pill.textContent = st.running ? (st.current && st.current.account ? t("busyAcct", { name: st.current.account.name }) : t("busy")) : t("ready");

    // jadwal berikutnya
    const n = a.next;
    const defMsg = settings ? settings.message : "";
    if (!n) {
      setText("heroTime", "--:--");
      setText("heroSlot", t("noSchedule"));
      setText("heroMeta", t("noScheduleHint"));
    } else {
      setText("heroTime", n.time);
      setText("heroSlot", `${slotPart(n.time)} · ${recipText(a, n.contacts)}`);
      setText("heroMeta", n.message || defMsg);
    }

    // data hari ini
    const mine = history.filter((r) => r.account && r.account.id === currentId);
    const cur = st.running && st.current && st.current.account && st.current.account.id === currentId ? st.current : null;
    const sendRuns = (cur && cur.mode === "send" ? [cur] : []).concat(mine.filter((r) => r.mode === "send"));
    const slots = slotsOfToday(a);
    const isDone = (r) => r.status === "success" || r.status === "partial";
    const todaySlots = slots.map((s) => {
      const cands = sendRuns.filter((r) => r.label === s.time && r.trigger === "schedule" && dayOf(r.started_at) === today);
      const run = cands.find(isDone) || cands.find((r) => r.status === "running") || cands[0] || null;
      const status = run ? run.status : s.time < nowHm ? "missed" : "pending";
      return { s, run, status, done: !!run && isDone(run) };
    });

    renderStreak(sendRuns, today);
    renderGoal(a, todaySlots);
    renderWeek(a, sendRuns, today, todaySlots, slots.length);
    renderStatusWidgets(a);
    renderTodayList(a, todaySlots);
    renderCookieBanner(a.cookies);
    renderHistory();
  }

  function renderStreak(sendRuns, today) {
    const days = new Set(sendRuns.filter((r) => r.sent > 0).map((r) => dayOf(r.started_at)));
    let day = days.has(today) ? today : addDays(today, -1);
    let n = 0;
    while (days.has(day)) { n++; day = addDays(day, -1); }
    setText("streakNum", String(n));
  }

  function renderGoal(a, todaySlots) {
    const total = todaySlots.length;
    const done = todaySlots.filter((x) => x.done).length;
    let sent = 0, targeted = 0;
    todaySlots.forEach((x) => {
      sent += x.run ? x.run.sent || 0 : 0;
      targeted += x.done ? x.run.total : expectedCount(a, x.s);
    });
    setText("goalSched", `${done}/${total}`);
    setText("goalContacts", `${sent}/${targeted}`);
    $("goalFg").setAttribute("stroke-dashoffset", String(351.9 * (1 - (total ? done / total : 0))));
  }

  function renderWeek(a, sendRuns, today, todaySlots, scheduleCount) {
    const box = $("weekDays");
    box.replaceChildren();
    let good = 0;
    const fmt = new Intl.DateTimeFormat(LOCALE[lang], { weekday: "short", timeZone: "UTC" });
    for (let i = 6; i >= 0; i--) {
      const day = addDays(today, -i);
      const isToday = i === 0;
      const runs = sendRuns.filter((r) => r.status !== "running" && dayOf(r.started_at) === day);
      let state, style = "";
      const pending = isToday && scheduleCount > 0 && todaySlots.some((x) => !x.done);
      if (pending) {
        state = "ring-day";
        style = `${Math.round((todaySlots.filter((x) => x.done).length / scheduleCount) * 100)}%`;
      } else if (runs.length) {
        const anySent = runs.some((r) => r.sent > 0);
        state = !anySent ? "failed" : runs.every((r) => r.total > 0 && r.sent >= r.total) ? "success" : "partial";
      } else {
        state = scheduleCount === 0 ? "rest" : "none";
      }
      if (state === "success") good++;
      const dot = el("span", { className: "dot " + state });
      if (style) dot.style.setProperty("--p", style);
      if (state === "success") dot.append(icon("i-check"));
      else if (state === "partial") dot.append(icon("i-bang"));
      else if (state === "failed") dot.append(icon("i-x"));
      else if (state === "rest") dot.textContent = "zz";
      box.append(el("div", { className: "day" + (isToday ? " today" : "") }, [dot, el("span", { className: "lbl", textContent: titleCase(fmt.format(dayDate(day))) })]));
    }
    setText("weekStat", `${good}/7`);
  }

  function renderStatusWidgets(a) {
    const c = a.cookies;
    const bad = c.invalid || !c.present;
    $("cookieIcon").className = "w-icon " + (c.invalid ? "red" : !c.present ? "" : "green");
    setText("cookieValue", t(c.invalid ? "cookieInvalid" : !c.present ? "cookieUnset" : "cookieValid"));
    setText("cookieSub", c.invalid ? c.invalid : !c.present ? "" : c.last_ok ? t("checkedAgo", { when: relTime(c.last_ok) }) : t("notVerified"));
    void bad;
    if (settings) {
      const ka = settings.keepalive_enabled;
      setText("refreshValue", ka ? tn("refreshEvery", settings.keepalive_hours) : t("refreshOff"));
      setText("refreshSub", ka ? t("refreshOn") : t("refreshOffSub"));
      const names = [];
      if (settings.discord_enabled && settings.discord_webhook_set) names.push("Discord");
      if (settings.telegram_enabled && settings.telegram_token_set && settings.telegram_chat_id) names.push("Telegram");
      setText("notifValue", names.length ? names.join(" & ") : t("notifOff"));
      setText("notifSub", names.length ? t(settings.notify_screenshot ? "notifShot" : "notifNoShot") : t("notifNone"));
    }
    setText("accountsValue", tn("nAccounts", accounts.length));
    setText("accountsSub", t("totalContacts", { n: accounts.reduce((s, x) => s + x.contacts, 0) }));
  }

  function evidenceText(ev) {
    if (!ev) return "";
    const p = [];
    if (ev.chat) p.push(t("evChat"));
    if (ev.bubble) p.push(t("evBubble"));
    if (ev.list_time) p.push(t("evList", { time: ev.list_time }));
    if (ev.renamed_to) p.push(t("evRenamed", { name: ev.renamed_to }));
    return p.join(" · ");
  }

  function contactRow(name, res) {
    const ok = res && res.ok;
    const fail = res && !res.ok;
    const dot = el("span", { className: "sdot" + (ok ? " success" : fail ? " failed" : "") });
    if (ok) dot.append(icon("i-check")); else if (fail) dot.append(icon("i-x"));
    let detail = "";
    if (ok) detail = evidenceText(res.evidence);
    else if (fail) detail = res.error || "";
    const time = res && res.sent_at ? res.sent_at.slice(0, 5) : "";
    return el("div", { className: "crow" }, [dot, el("span", { className: "name", textContent: name }),
      el("span", { className: "detail", textContent: detail }), el("span", { className: "time", textContent: time })]);
  }

  function renderTodayList(a, todaySlots) {
    const box = $("todayList");
    box.replaceChildren();
    setText("todayCount", tn("nSchedules", todaySlots.length));
    if (!todaySlots.length) {
      box.append(el("p", { className: "empty", textContent: t("emptyToday") }));
      return;
    }
    todaySlots.forEach(({ s, run, status }) => {
      const head = el("div", { className: "slot-head" }, [
        el("div", {}, [el("span", { className: "slot-time", textContent: s.time }),
          el("span", { className: "muted", textContent: `${slotPart(s.time)} · ${recipText(a, s.contacts)}` })]),
        badge(status),
      ]);
      const slot = el("div", { className: "slot" }, [head]);
      const names = s.contacts == null ? contactList : s.contacts;
      const results = run ? run.results || [] : [];
      const seen = new Set();
      results.forEach((r) => { seen.add(r.contact.toLowerCase()); slot.append(contactRow(r.contact, r)); });
      names.filter((c) => !seen.has(c.toLowerCase())).forEach((c) => slot.append(contactRow(c, null)));
      box.append(slot);
    });
  }

  // ------------------------------------------------------------ log & history
  async function refresh() {
    try {
      const [s, cur] = await Promise.all([api("/status"), api("/run/current?since=" + logCursor)]);
      st = s;
      serverNow = s.server_now || serverNow;
      if (syncAccounts(s.accounts)) { await switchAccount(currentId); return; }
      renderDashboard();
      $("btnSend").disabled = $("btnTest").disabled = s.running;
      $("btnStop").classList.toggle("hidden", !s.running);

      if (cur.run) {
        if (cur.run.id !== lastRunId) {
          lastRunId = cur.run.id;
          logCursor = 0;
          pinned = false;
          $("logBox").textContent = "";
          idleLogKey = null;
          return refresh();
        }
        if (!pinned) {
          appendLogs(cur.logs);
          setRunBadge(cur.run.status);
        }
        logCursor = cur.next;
        if (!s.running && wasRunning) await loadHistory();
      } else renderIdleLog();
      wasRunning = s.running;
    } catch (e) { /* 401 ditangani di api() */ }
  }

  // Tanpa proses berjalan: tampilkan log proses terakhir dari riwayat (atau keterangan kosong)
  let idleLogKey = null;
  function renderIdleLog() {
    if (pinned || lastRunId) return;
    const last = history[0];
    const key = last ? last.id : "none:" + lang;
    if (key === idleLogKey) return;
    idleLogKey = key;
    const box = $("logBox");
    box.replaceChildren();
    if (last) {
      (last.logs || []).forEach((l) => box.append(logLine(l)));
      setRunBadge(last.status);
      box.scrollTop = box.scrollHeight;
    } else {
      box.append(el("div", { className: "log-empty", textContent: t("noRuns") }));
      setRunBadge("");
    }
  }

  function setRunBadge(status) {
    const b = $("runBadge");
    b.className = "badge " + status;
    b.textContent = status ? statusLabel(status) : "";
    b.dataset.status = status || "";
  }

  function logLine(l) { return el("div", { className: l.level, textContent: `[${l.t}] ${l.msg}` }); }
  function appendLogs(lines) {
    if (!lines.length) return;
    const box = $("logBox");
    const atBottom = box.scrollTop + box.clientHeight >= box.scrollHeight - 20;
    lines.forEach((l) => box.append(logLine(l)));
    if (atBottom) box.scrollTop = box.scrollHeight;
  }

  async function startRun(mode) {
    $("runErr").textContent = "";
    try {
      await api("/run", { method: "POST", body: { mode, account: currentId, message: $("runMessage").value.trim() || null } });
      await refresh();
    } catch (e) { $("runErr").textContent = e.message; }
  }
  $("btnSend").addEventListener("click", () => {
    if (confirm(t("confirmSend", { name: curAccount().name }))) startRun("send");
  });
  $("btnTest").addEventListener("click", () => startRun("test"));
  $("btnStop").addEventListener("click", () => api("/run/stop", { method: "POST" }).then(() => toast(t("toastStopping"))).catch((e) => toast(e.message)));

  // ------------------------------------------------------------- lightbox
  const lb = { items: [], index: 0, trigger: null, open: false };
  function buildLightbox() {
    const caption = el("span", { className: "lb-caption" });
    const dl = el("a", { className: "lb-btn", id: "lbDownload" });
    const close = el("button", { className: "lb-btn lb-close", type: "button", id: "lbClose" }, [icon("i-x")]);
    const prev = el("button", { className: "lb-nav prev", type: "button", id: "lbPrev" }, [icon("i-chev")]);
    const next = el("button", { className: "lb-nav next", type: "button", id: "lbNext" }, [icon("i-chev")]);
    const img = el("img", { id: "lbImg", draggable: false, alt: "" });
    const stage = el("div", { className: "lb-stage" }, [img]);
    const root = el("div", { id: "lightbox", className: "lightbox hidden", role: "dialog", "aria-modal": "true" }, [
      el("div", { className: "lb-bar" }, [caption, dl, close]), prev, next, stage]);
    document.body.append(root);
    root.addEventListener("click", (e) => { if (e.target === root || e.target === stage) closeLightbox(); });
    close.addEventListener("click", closeLightbox);
    prev.addEventListener("click", () => stepLightbox(-1));
    next.addEventListener("click", () => stepLightbox(1));
    img.addEventListener("click", () => { stage.classList.toggle("zoom"); updateZoomHint(); });
    return root;
  }
  const lightboxEl = buildLightbox();

  function updateZoomHint() {
    const zoomed = lightboxEl.querySelector(".lb-stage").classList.contains("zoom");
    $("lbImg").title = t(zoomed ? "lbZoomOut" : "lbZoomIn");
  }
  function showLightboxItem() {
    const it = lb.items[lb.index];
    const n = lb.items.length;
    const cap = n > 1 ? `${it.caption} (${lb.index + 1}/${n})` : it.caption;
    lightboxEl.querySelector(".lb-caption").textContent = cap;
    lightboxEl.setAttribute("aria-label", cap);
    $("lbImg").src = it.url;
    $("lbImg").alt = it.caption;
    lightboxEl.querySelector(".lb-stage").classList.remove("zoom");
    lightboxEl.querySelector(".lb-stage").scrollTo(0, 0);
    updateZoomHint();
    const dl = $("lbDownload");
    dl.href = it.url;
    dl.download = it.filename;
    dl.textContent = t("lbDownload");
    $("lbClose").setAttribute("aria-label", t("lbClose"));
    $("lbClose").title = t("lbClose");
    $("lbPrev").setAttribute("aria-label", t("lbPrev"));
    $("lbNext").setAttribute("aria-label", t("lbNext"));
    $("lbPrev").classList.toggle("hidden", n < 2);
    $("lbNext").classList.toggle("hidden", n < 2);
  }
  function stepLightbox(d) {
    const n = lb.items.length;
    if (n < 2) return;
    lb.index = (lb.index + d + n) % n;
    showLightboxItem();
  }
  // items: [{url, caption, filename, revoke}]; trigger: elemen yang mendapat fokus kembali
  function openLightbox(items, index, trigger) {
    lb.items = items;
    lb.index = index || 0;
    lb.trigger = trigger || document.activeElement;
    lb.open = true;
    showLightboxItem();
    lightboxEl.classList.remove("hidden");
    document.body.style.overflow = "hidden";
    $("lbClose").focus();
  }
  function closeLightbox() {
    if (!lb.open) return;
    lb.open = false;
    lightboxEl.classList.add("hidden");
    document.body.style.overflow = "";
    $("lbImg").removeAttribute("src");
    lb.items.forEach((it) => { if (it.revoke) URL.revokeObjectURL(it.url); });
    lb.items = [];
    if (lb.trigger && lb.trigger.focus) lb.trigger.focus();
  }
  document.addEventListener("keydown", (e) => {
    if (!lb.open) return;
    if (e.key === "Escape") { e.preventDefault(); closeLightbox(); }
    else if (e.key === "ArrowLeft") stepLightbox(-1);
    else if (e.key === "ArrowRight") stepLightbox(1);
    else if (e.key === "Tab") {
      const f = [...lightboxEl.querySelectorAll("a[href], button")].filter((x) => !x.classList.contains("hidden"));
      const first = f[0], last = f[f.length - 1];
      if (!lightboxEl.contains(document.activeElement)) { e.preventDefault(); first.focus(); }
      else if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

  $("btnShot").addEventListener("click", async () => {
    const btn = $("btnShot");
    try {
      const res = await fetch("/api/run/screenshot?t=" + Date.now(), { headers: { "X-API-Key": apiKey } });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.status);
      const url = URL.createObjectURL(await res.blob());
      openLightbox([{ url, caption: t("lbLatestShot"), filename: "streak-screenshot.jpg", revoke: true }], 0, btn);
    } catch (e) { toast(e.message); }
  });

  let proofUrls = [];
  let proofToken = 0;
  async function showProofs(run) {
    const box = $("proofBox");
    const token = ++proofToken;
    proofUrls.forEach((u) => URL.revokeObjectURL(u));
    proofUrls = [];
    box.replaceChildren();
    const items = [];
    for (const r of run.results || []) {
      if (!r.proof) continue;
      try {
        const res = await fetch(`/api/proof/${run.id}/${r.proof}`, { headers: { "X-API-Key": apiKey } });
        if (!res.ok) continue;
        const blob = await res.blob();
        if (token !== proofToken) return;
        const url = URL.createObjectURL(blob);
        proofUrls.push(url);
        const cap = `${r.contact} ${r.sent_at || ""}`.trim();
        items.push({ url, caption: cap, filename: `${r.contact}-${run.id}-${r.proof}`.replace(/[^\w.-]+/g, "_") });
        const idx = items.length - 1;
        const img = el("img", { src: url, alt: t("proofAlt", { name: r.contact }) });
        const btn = el("button", { className: "proof-btn", type: "button", "aria-label": t("proofAlt", { name: r.contact }) }, [img]);
        btn.addEventListener("click", () => openLightbox(items, idx, btn));
        box.append(el("figure", {}, [btn, el("figcaption", { textContent: `${r.contact} — ${r.sent_at || ""}` })]));
      } catch (e) { /* abaikan */ }
    }
  }

  async function loadHistory() {
    const { runs } = await api("/history");
    history = runs;
    renderIdleLog();
    renderHistory();
    renderDashboard();
  }

  function renderHistory() {
    const body = $("historyBody");
    body.replaceChildren();
    if (!history.length) {
      body.append(el("tr", {}, [el("td", { colSpan: 6, className: "muted", textContent: t("noHistory") })]));
      return;
    }
    history.forEach((r) => {
      const type = { test: t("typeTest"), check: t("typeCheck") }[r.mode] || t("typeSend");
      const how = r.trigger === "schedule" ? r.label || "" : r.trigger === "keepalive" ? t("trAuto") : t("trManual");
      const tr = el("tr", { tabIndex: 0, title: t("clickForLog") }, [
        el("td", { textContent: fmtDateTime(r.started_at) }),
        el("td", { textContent: (r.account && r.account.name) || "-" }),
        el("td", { textContent: how ? `${type} · ${how}` : type }),
        el("td", { className: "num", textContent: r.mode === "check" ? "-" : `${r.sent}/${r.total}` }),
        el("td", { className: "num", textContent: duration(r) }),
        el("td", {}, [badge(r.status)]),
      ]);
      const open = () => {
        const box = $("logBox");
        box.replaceChildren();
        (r.logs || []).forEach((l) => box.append(logLine(l)));
        pinned = true;
        setRunBadge(r.status);
        showProofs(r);
        $("logBox").scrollIntoView({ behavior: "smooth", block: "center" });
      };
      tr.addEventListener("click", open);
      tr.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } });
      body.append(tr);
    });
  }
  $("clearHistory").addEventListener("click", async () => {
    if (!confirm(t("confirmClear"))) return;
    try { await api("/history", { method: "DELETE" }); await loadHistory(); } catch (e) { toast(e.message); }
  });

  // --------------------------------------------------------------- contacts
  async function loadContacts() {
    const { contacts } = await apiA("/contacts");
    renderContacts(contacts);
  }
  function renderContacts(contacts) {
    contactList = contacts;
    document.querySelectorAll(".sched").forEach((r) => r.setContacts && r.setContacts());
    setText("contactsCount", String(contacts.length));
    const ul = $("contactsList");
    ul.replaceChildren();
    if (!contacts.length) ul.append(el("li", { className: "muted", textContent: t("noContacts") }));
    contacts.forEach((c) => {
      const ren = el("button", { className: "btn plain small", type: "button", textContent: t("rename"), "aria-label": t("renameAria", { name: c }) });
      const del = el("button", { className: "btn plain small destructive-text", type: "button", textContent: t("del"), "aria-label": t("delAria", { name: c }) });
      del.addEventListener("click", async () => {
        try { renderContacts((await apiA("/contacts?name=" + encodeURIComponent(c), { method: "DELETE" })).contacts); await refresh(); }
        catch (e) { toast(e.message); }
      });
      ren.addEventListener("click", async () => {
        const name = prompt(t("promptRename"), c);
        if (!name || name.trim() === c) return;
        try {
          renderContacts((await apiA("/contacts/rename", { method: "PUT", body: { old: c, new: name } })).contacts);
          await refresh();
          renderSchedules(curAccount().schedules);
        } catch (e) { toast(e.message); }
      });
      ul.append(el("li", {}, [el("div", { className: "grow" }, [el("div", { className: "title", textContent: c })]), el("div", { className: "actions" }, [ren, del])]));
    });
    dashSig = "";
    renderDashboard();
  }
  $("btnAddContacts").addEventListener("click", async () => {
    $("contactsErr").textContent = "";
    try {
      const r = await apiA("/contacts", { method: "POST", body: { names: $("contactsInput").value } });
      $("contactsInput").value = "";
      renderContacts(r.contacts);
      await refresh();
      toast(t("toastAdded", { n: r.added.length }));
    } catch (e) { $("contactsErr").textContent = e.message; }
  });

  // ---------------------------------------------------------------- cookies
  function renderCookieBanner(c) {
    const box = $("cookieBanner");
    const kind = c.invalid ? "bad" : !c.present ? "none" : "ok";
    box.className = "banner " + kind;
    let title, sub;
    if (kind === "bad") { title = t("bannerBad"); sub = c.invalid; }
    else if (kind === "none") { title = t("bannerNone"); sub = t("bannerNoneSub"); }
    else {
      title = t("bannerOk");
      const p = [t("cookieCount", { n: c.count }), c.last_ok ? t("checkedAgo", { when: relTime(c.last_ok) }) : t("notVerified")];
      if (c.last_saved) p.push(t("savedAgo", { when: relTime(c.last_saved) }));
      if (!c.has_session) p.push(t("warnNoSession"));
      sub = p.join(" · ");
    }
    box.replaceChildren(
      el("span", { className: "b-icon" }, [icon(kind === "ok" ? "i-check" : kind === "bad" ? "i-x" : "i-key")]),
      el("span", {}, [el("span", { className: "b-title", textContent: title }), el("br"), el("span", { className: "b-sub", textContent: sub })]),
    );
  }

  $("btnCheckCookies").addEventListener("click", async () => {
    $("cookieErr").textContent = "";
    try {
      await api("/run", { method: "POST", body: { mode: "check", account: currentId } });
      toast(t("toastChecking"));
      await refresh();
    } catch (e) { $("cookieErr").textContent = e.message; }
  });
  $("btnSaveCookies").addEventListener("click", async () => {
    $("cookieErr").textContent = "";
    try {
      await apiA("/cookies", { method: "PUT", body: { raw: $("cookieInput").value } });
      $("cookieInput").value = "";
      toast(t("toastCookieSaved"));
      await refresh();
    } catch (e) { $("cookieErr").textContent = e.message; }
  });
  $("btnClearCookies").addEventListener("click", async () => {
    if (!confirm(t("confirmClearCookies"))) return;
    try { await apiA("/cookies", { method: "DELETE" }); await refresh(); } catch (e) { toast(e.message); }
  });

  // ----------------------------------------------------------- remote login
  const view = $("remoteView");

  function renderLoginSteps() {
    const cls = loginMode === "idle" ? ["now", "", ""] : loginMode === "open" ? ["done", "now", ""] : ["done", "done", "now"];
    $("loginSteps").replaceChildren(...["step1", "step2", "step3"].map((k, i) =>
      el("li", { className: cls[i] }, [el("span", { className: "n", textContent: String(i + 1) }), t(k)])));
  }
  function renderLoginMsg() {
    const box = $("loginStateBox");
    const txt = loginMsg ? (loginMsg.raw || t(loginMsg.key, loginMsg.vars)) : "";
    setText("loginState", txt);
    box.classList.toggle("hidden", !txt);
    box.classList.toggle("warn", !!loginMsg && loginMsg.cls === "warn");
    box.classList.toggle("ok", !!loginMsg && loginMsg.cls === "ok");
  }
  function setLoginMsg(key, cls, vars) { loginMsg = key ? { key, vars, cls } : null; renderLoginMsg(); }

  function setLoginUi(active) {
    $("remoteIdle").classList.toggle("hidden", active);
    $("remoteWrap").classList.toggle("hidden", !active);
    $("btnLoginSave").classList.toggle("hidden", !active);
    $("btnLoginStop").classList.toggle("hidden", !active);
  }

  async function pullFrame() {
    if (framePending) return;
    framePending = true;
    try {
      const res = await fetch("/api/login/frame?t=" + Date.now(), { headers: { "X-API-Key": apiKey } });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.status);
      const url = URL.createObjectURL(await res.blob());
      const old = view.src;
      view.src = url;
      if (old.startsWith("blob:")) URL.revokeObjectURL(old);
    } catch (e) {
      if (loginMode !== "idle") endLogin("loginEnded");
    } finally { framePending = false; }
  }

  async function pullStatus() {
    try {
      const s = await api("/login/status");
      if (loginMode === "idle") return;
      if (!s.active) return endLogin("loginEnded");
      loginMode = s.logged_in ? "logged" : "open";
      renderLoginSteps();
      if (s.logged_in) setLoginMsg("loginDetected", "ok"); else setLoginMsg("loginWaiting", "warn");
    } catch (e) { /* diabaikan */ }
  }

  function endLogin(key, cls, vars) {
    clearInterval(loginTimer);
    loginTimer = null;
    loginMode = "idle";
    setLoginUi(false);
    renderLoginSteps();
    setLoginMsg(key, cls, vars);
  }

  $("btnLoginStart").addEventListener("click", async () => {
    $("cookieErr").textContent = "";
    setLoginMsg("loginOpening", "warn");
    try {
      await apiA("/login/start", { method: "POST" });
      loginMode = "open";
      setLoginUi(true);
      renderLoginSteps();
      setLoginMsg("loginWaiting", "warn");
      clearInterval(loginTimer);
      let n = 0;
      loginTimer = setInterval(() => { pullFrame(); if (++n % 5 === 0) pullStatus(); }, 700);
      pullFrame();
    } catch (e) { setLoginMsg(null); $("cookieErr").textContent = e.message; }
  });

  $("btnLoginStop").addEventListener("click", async () => {
    await api("/login/stop", { method: "POST" }).catch(() => {});
    endLogin("loginCancelled");
  });

  $("btnLoginSave").addEventListener("click", async () => {
    $("cookieErr").textContent = "";
    try {
      const r = await api("/login/save", { method: "POST" });
      endLogin("loginSaved", "ok", { n: r.saved });
      toast(t("toastLoginSaved"));
      await refresh();
    } catch (e) { $("cookieErr").textContent = e.message; }
  });

  function coords(ev) {
    const r = view.getBoundingClientRect();
    return { x: (ev.clientX - r.left) * view.naturalWidth / r.width, y: (ev.clientY - r.top) * view.naturalHeight / r.height };
  }
  const send = (body) => api("/login/input", { method: "POST", body }).catch(() => {});

  view.addEventListener("click", (e) => { view.focus(); send({ type: "click", ...coords(e) }); });
  view.addEventListener("wheel", (e) => {
    e.preventDefault();
    send({ type: "scroll", ...coords(e), dx: e.deltaX, dy: e.deltaY });
  }, { passive: false });
  view.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return; // biar paste lewat kolom teks
    if (e.key.length === 1 || ["Backspace", "Tab", "Enter", "Escape", "Delete", "Home", "End", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) {
      e.preventDefault();
      send({ type: "key", key: e.key });
    }
  });
  view.addEventListener("paste", (e) => {
    e.preventDefault();
    send({ type: "text", text: e.clipboardData.getData("text") });
  });
  $("remoteText").addEventListener("keydown", async (e) => {
    if (e.key !== "Enter") return;
    const v = e.target.value;
    e.target.value = "";
    if (v) await send({ type: "text", text: v });
  });

  // ------------------------------------------------------- schedules editor
  const options = (n, val, label) => {
    const sel = el("select", { "aria-label": label });
    for (let i = 0; i < n; i++) sel.append(new Option(pad(i), pad(i)));
    sel.value = val;
    return sel;
  };

  function addScheduleRow(sc = { id: "", enabled: true, time: "07:00", message: "", contacts: null }) {
    const [hh, mm] = sc.time.split(":");
    const enabled = el("input", { type: "checkbox", className: "switch", checked: sc.enabled, role: "switch", "aria-label": t("schedEnabled") });
    const hour = options(24, hh, t("hour")), min = options(60, mm, t("minute"));
    const title = el("div", { className: "title" });
    const meta = el("div", { className: "meta" });
    const del = el("button", { className: "btn plain small destructive-text", type: "button", textContent: t("del") });
    const msg = el("input", { type: "text", value: sc.message || "", placeholder: t("schedMsgPh"), maxLength: 500, "aria-label": t("schedMsgPh") });

    // Penerima: semua kontak akun, atau hanya yang dicentang
    const allBox = el("input", { type: "checkbox", className: "switch", checked: sc.contacts == null, role: "switch" });
    const chips = el("div", { className: "chips" });
    const selected = new Set((sc.contacts || []).map((c) => c.toLowerCase()));
    const head = () => {
      title.textContent = partName(+hour.value);
      meta.textContent = allBox.checked ? t("allContacts", { n: contactList.length })
        : tn("nContacts", contactList.filter((c) => selected.has(c.toLowerCase())).length);
      del.setAttribute("aria-label", t("delSched", { time: `${hour.value}:${min.value}` }));
    };
    const buildChips = () => {
      chips.replaceChildren();
      contactList.forEach((c) => {
        const key = c.toLowerCase();
        const cb = el("input", { type: "checkbox", checked: selected.has(key) });
        cb.addEventListener("change", () => { if (cb.checked) selected.add(key); else selected.delete(key); head(); });
        chips.append(el("label", { className: "chip" }, [cb, icon("i-check", "tick"), el("span", { textContent: c })]));
      });
      if (!contactList.length) chips.append(el("span", { className: "muted", textContent: t("noContactsHere") }));
      chips.classList.toggle("hidden", allBox.checked);
      head();
    };
    allBox.addEventListener("change", buildChips);
    hour.addEventListener("change", head);
    min.addEventListener("change", head);
    buildChips();

    const row = el("div", { className: "sched" + (sc.enabled ? "" : " off") }, [
      el("div", { className: "sched-top" }, [
        enabled,
        el("div", { className: "time-pick" }, [hour, el("span", { textContent: ":" }), min]),
        el("div", { className: "grow" }, [title, meta]),
        del,
      ]),
      msg,
      el("label", { className: "switch-row" }, [el("span", { textContent: t("sendToAll") }), allBox]),
      chips,
    ]);
    row.setContacts = buildChips;
    row.dataset.id = sc.id || "";
    enabled.addEventListener("change", () => row.classList.toggle("off", !enabled.checked));
    del.addEventListener("click", () => { row.remove(); syncSchedEmpty(); });
    row.read = () => ({
      id: row.dataset.id || null,
      enabled: enabled.checked,
      time: `${hour.value}:${min.value}`,
      message: msg.value.trim(),
      contacts: allBox.checked ? null : contactList.filter((c) => selected.has(c.toLowerCase())),
    });
    $("scheduleList").append(row);
  }

  function syncSchedEmpty() {
    const box = $("scheduleList");
    const empty = box.querySelector(".empty");
    const has = box.querySelector(".sched");
    if (!has && !empty) box.append(el("p", { className: "empty", textContent: t("noScheds") }));
    else if (has && empty) empty.remove();
  }

  function renderSchedules(list) {
    $("scheduleList").replaceChildren();
    list.forEach(addScheduleRow);
    syncSchedEmpty();
  }
  const readSchedules = () => [...$("scheduleList").querySelectorAll(".sched")].map((r) => r.read());

  $("btnAddSchedule").addEventListener("click", () => {
    if ($("scheduleList").querySelectorAll(".sched").length >= 8) return toast(t("maxSchedules"));
    $("scheduleList").querySelector(".empty")?.remove();
    addScheduleRow();
  });

  $("btnSaveSchedules").addEventListener("click", async () => {
    try {
      const acc = await api("/accounts/" + currentId, { method: "PUT", body: { schedules: readSchedules() } });
      renderSchedules(acc.schedules);
      setMsg("scheduleMsg", "", "schedulesSaveHint");
      toast(t("toastSchedulesSaved"));
      await refresh();
    } catch (e) { setMsg("scheduleMsg", e.message); }
  });

  // --------------------------------------------------------------- settings
  async function loadSettings() {
    const s = await api("/settings");
    settings = s;
    $("setMessage").value = s.message;
    $("setTimezone").value = s.timezone;
    $("setNotifyShot").checked = s.notify_screenshot;
    $("setKeepalive").checked = s.keepalive_enabled;
    $("setKeepaliveHours").value = s.keepalive_hours;
    $("setPageWait").value = s.page_load_wait;
    $("setElementWait").value = s.element_wait;
    $("setSendDelay").value = s.send_delay;
    $("setTgEnabled").checked = s.telegram_enabled;
    $("setTgChat").value = s.telegram_chat_id;
    $("setTgToken").value = "";
    $("setDcEnabled").checked = s.discord_enabled;
    $("setDcWebhook").value = "";
    renderSettingsStates();
    $("tzLabel").textContent = t("tzLabel", { tz: s.timezone || t("tzServer") });
    renderDashboard();
  }
  function renderSettingsStates() {
    if (!settings) return;
    setText("dcWebhookState", settings.discord_webhook_set ? t("saved") : "");
    setText("tgTokenState", settings.telegram_token_set ? t("saved") : "");
    $("tzLabel").textContent = t("tzLabel", { tz: settings.timezone || t("tzServer") });
  }
  $("settingsForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api("/settings", {
        method: "PUT",
        body: {
          message: $("setMessage").value,
          timezone: $("setTimezone").value.trim(),
          notify_screenshot: $("setNotifyShot").checked,
          keepalive_enabled: $("setKeepalive").checked,
          keepalive_hours: +$("setKeepaliveHours").value,
          page_load_wait: +$("setPageWait").value,
          element_wait: +$("setElementWait").value,
          send_delay: +$("setSendDelay").value,
          discord_enabled: $("setDcEnabled").checked,
          discord_webhook: $("setDcWebhook").value.trim(),
          telegram_enabled: $("setTgEnabled").checked,
          telegram_token: $("setTgToken").value.trim(),
          telegram_chat_id: $("setTgChat").value.trim(),
        },
      });
      await loadSettings();
      setText("settingsMsg", "");
      toast(t("toastSettingsSaved"));
      await refresh();
    } catch (err) { setText("settingsMsg", err.message); }
  });
  const testHook = (path) => async () => {
    try { await api(path, { method: "POST" }); toast(t("toastTestSent")); }
    catch (e) { toast(e.message); }
  };
  $("btnDcTest").addEventListener("click", testHook("/discord/test"));
  $("btnTgTest").addEventListener("click", testHook("/telegram/test"));

  // ----------------------------------------------------------- render semua
  function renderAll() {
    renderLoginSteps();
    renderLoginMsg();
    if (!accounts.length) return;
    dashSig = "";
    renderAccountList(true);
    renderDashboard(true);
    renderContacts(contactList);
    renderSettingsStates();
    const b = $("runBadge");
    if (b.dataset.status) b.textContent = statusLabel(b.dataset.status);
    idleLogKey = null;
    renderIdleLog();
    if (lb.open) showLightboxItem();
    if (!$("app").classList.contains("hidden")) renderSchedules(readSchedules());
  }

  // ------------------------------------------------------------------ start
  document.documentElement.lang = lang;
  document.querySelectorAll(".segmented [data-lang]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === lang)));
  applyStaticI18n();
  renderLoginSteps();
  renderLoginMsg();
  showTab("dashboard");
  if (apiKey) enter().catch(showLogin); else showLogin();
})();
