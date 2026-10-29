(() => {
  const $ = (id) => document.getElementById(id);
  const KEY = "streak_panel_key";
  let apiKey = "";
  let logCursor = 0;
  let lastRunId = null;
  let pinned = false; // true saat melihat log dari riwayat
  let pollTimer = null;

  try { apiKey = localStorage.getItem(KEY) || ""; } catch (e) { /* storage tidak tersedia */ }

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

  function toast(msg) {
    const t = $("toast");
    t.textContent = msg;
    t.classList.remove("hidden");
    clearTimeout(toast.t);
    toast.t = setTimeout(() => t.classList.add("hidden"), 2500);
  }

  function setText(id, text) { $(id).textContent = text; }

  function fmtTime(iso) {
    if (!iso) return "-";
    const d = new Date(iso);
    return isNaN(d) ? iso : d.toLocaleString();
  }

  function el(tag, props = {}, children = []) {
    const n = document.createElement(tag);
    Object.assign(n, props);
    children.forEach((c) => n.append(c));
    return n;
  }

  const STATUS_LABEL = {
    running: "Berjalan", success: "Berhasil", partial: "Sebagian", failed: "Gagal", cancelled: "Dihentikan",
  };

  function badge(status) {
    return el("span", { className: "badge " + status, textContent: STATUS_LABEL[status] || status });
  }

  // ------------------------------------------------------------------- auth
  function showLogin() {
    $("app").classList.add("hidden");
    $("login").classList.remove("hidden");
    clearInterval(pollTimer);
  }

  async function enter() {
    await api("/status");
    $("login").classList.add("hidden");
    $("app").classList.remove("hidden");
    await Promise.all([loadSettings(), loadContacts(), loadCookies(), loadHistory()]);
    await refresh();
    clearInterval(pollTimer);
    pollTimer = setInterval(refresh, 2000);
  }

  $("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    apiKey = $("keyInput").value.trim();
    $("loginErr").textContent = "";
    try {
      await enter();
      try { localStorage.setItem(KEY, apiKey); } catch (err) { /* abaikan */ }
    } catch (err) {
      $("loginErr").textContent = "Access key salah.";
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
  $("tabs").addEventListener("click", (e) => {
    const tab = e.target.dataset.tab;
    if (!tab) return;
    document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("active", b === e.target));
    document.querySelectorAll("main > section").forEach((s) => s.classList.toggle("hidden", s.id !== "tab-" + tab));
  });

  // -------------------------------------------------------------- dashboard
  async function refresh() {
    try {
      const [st, cur] = await Promise.all([api("/status"), api("/run/current?since=" + logCursor)]);
      setText("stState", st.running ? "Berjalan…" : "Siap");
      setText("stContacts", st.contacts);
      renderCookieState(st.cookies);
      setText("stCookies", st.cookies.invalid ? "⚠️ Tidak valid" : !st.cookies.present ? "Belum diatur" : st.cookies.has_session ? `${st.cookies.count} (sessionid ✓)` : `${st.cookies.count} (tanpa sessionid)`);
      setText("stNext", st.next_run ? st.next_run : st.schedule_enabled ? "-" : "Nonaktif");
      $("btnSend").disabled = $("btnTest").disabled = st.running;
      $("btnStop").classList.toggle("hidden", !st.running);

      if (cur.run) {
        if (cur.run.id !== lastRunId) {
          lastRunId = cur.run.id;
          logCursor = 0;
          pinned = false;
          $("logBox").textContent = "";
          return refresh();
        }
        if (!pinned) appendLogs(cur.logs);
        logCursor = cur.next;
        const b = $("runBadge");
        b.className = "badge " + cur.run.status;
        b.textContent = STATUS_LABEL[cur.run.status] || cur.run.status;
        if (!st.running && refresh.wasRunning) loadHistory();
      }
      refresh.wasRunning = st.running;
    } catch (e) { /* 401 ditangani di api() */ }
  }

  function appendLogs(lines) {
    if (!lines.length) return;
    const box = $("logBox");
    const atBottom = box.scrollTop + box.clientHeight >= box.scrollHeight - 20;
    lines.forEach((l) => {
      box.append(el("div", { className: l.level, textContent: `[${l.t}] ${l.msg}` }));
    });
    if (atBottom) box.scrollTop = box.scrollHeight;
  }

  async function startRun(mode) {
    $("runErr").textContent = "";
    try {
      await api("/run", { method: "POST", body: { mode, message: $("runMessage").value.trim() || null } });
      await refresh();
    } catch (e) { $("runErr").textContent = e.message; }
  }
  $("btnSend").addEventListener("click", () => {
    if (confirm("Kirim pesan streak ke semua kontak sekarang?")) startRun("send");
  });
  $("btnTest").addEventListener("click", () => startRun("test"));
  $("btnStop").addEventListener("click", () => api("/run/stop", { method: "POST" }).then(() => toast("Menghentikan…")));

  $("btnShot").addEventListener("click", async () => {
    const img = $("shotView");
    try {
      const res = await fetch("/api/run/screenshot?t=" + Date.now(), { headers: { "X-API-Key": apiKey } });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.status);
      if (img.src.startsWith("blob:")) URL.revokeObjectURL(img.src);
      img.src = URL.createObjectURL(await res.blob());
      img.classList.remove("hidden");
    } catch (e) { toast(e.message); }
  });

  async function loadHistory() {
    const { runs } = await api("/history");
    const body = $("historyBody");
    body.replaceChildren();
    if (!runs.length) {
      body.append(el("tr", {}, [el("td", { colSpan: 5, className: "muted", textContent: "Belum ada riwayat." })]));
      return;
    }
    runs.forEach((r) => {
      const tr = el("tr", {}, [
        el("td", { textContent: fmtTime(r.started_at) }),
        el("td", { textContent: { test: "Uji", check: "Cek cookie" }[r.mode] || "Kirim" }),
        el("td", { textContent: { schedule: "Jadwal", keepalive: "Otomatis" }[r.trigger] || "Manual" }),
        el("td", { textContent: `${r.sent}/${r.total}` }),
        el("td", {}, [badge(r.status)]),
      ]);
      tr.style.cursor = "pointer";
      tr.title = "Klik untuk melihat log";
      tr.addEventListener("click", () => {
        const box = $("logBox");
        box.replaceChildren();
        (r.logs || []).forEach((l) => box.append(el("div", { className: l.level, textContent: `[${l.t}] ${l.msg}` })));
        pinned = true;
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
      body.append(tr);
    });
  }
  $("clearHistory").addEventListener("click", async () => {
    if (!confirm("Hapus semua riwayat?")) return;
    await api("/history", { method: "DELETE" });
    loadHistory();
  });

  // --------------------------------------------------------------- contacts
  async function loadContacts() {
    const { contacts } = await api("/contacts");
    renderContacts(contacts);
  }
  function renderContacts(contacts) {
    setText("contactsCount", contacts.length);
    const ul = $("contactsList");
    ul.replaceChildren();
    if (!contacts.length) ul.append(el("li", { className: "muted", textContent: "Belum ada kontak." }));
    contacts.forEach((c) => {
      const btn = el("button", { className: "btn danger small", textContent: "Hapus" });
      btn.addEventListener("click", async () => {
        try {
          const r = await api("/contacts?name=" + encodeURIComponent(c), { method: "DELETE" });
          renderContacts(r.contacts);
        } catch (e) { toast(e.message); }
      });
      ul.append(el("li", {}, [el("span", { textContent: c }), btn]));
    });
  }
  $("btnAddContacts").addEventListener("click", async () => {
    $("contactsErr").textContent = "";
    try {
      const r = await api("/contacts", { method: "POST", body: { names: $("contactsInput").value } });
      $("contactsInput").value = "";
      renderContacts(r.contacts);
      toast(`${r.added.length} kontak ditambahkan`);
    } catch (e) { $("contactsErr").textContent = e.message; }
  });

  // ---------------------------------------------------------------- cookies
  function renderCookieState(s) {
    let t = !s.present ? "Status: belum ada cookie." : `Status: ${s.count} cookie tersimpan${s.has_session ? " (sessionid ada)" : " — peringatan: sessionid tidak ditemukan"}.`;
    if (s.invalid) t += ` ⚠️ Tidak valid: ${s.invalid}`;
    else if (s.last_ok) t += ` Terakhir terverifikasi: ${fmtTime(s.last_ok)}.`;
    if (s.last_saved) t += ` Terakhir diperbarui: ${fmtTime(s.last_saved)}.`;
    setText("cookieState", t);
  }
  $("btnCheckCookies").addEventListener("click", async () => {
    $("cookieErr").textContent = "";
    try {
      await api("/run", { method: "POST", body: { mode: "check" } });
      toast("Mengecek cookie… lihat log di Dashboard");
    } catch (e) { $("cookieErr").textContent = e.message; }
  });
  async function loadCookies() { renderCookieState(await api("/cookies")); }
  $("btnSaveCookies").addEventListener("click", async () => {
    $("cookieErr").textContent = "";
    try {
      renderCookieState(await api("/cookies", { method: "PUT", body: { raw: $("cookieInput").value } }));
      $("cookieInput").value = "";
      toast("Cookie disimpan");
    } catch (e) { $("cookieErr").textContent = e.message; }
  });
  $("btnClearCookies").addEventListener("click", async () => {
    if (!confirm("Hapus cookie tersimpan?")) return;
    renderCookieState(await api("/cookies", { method: "DELETE" }));
  });

  // ----------------------------------------------------------- remote login
  let loginTimer = null;
  let framePending = false;
  const view = $("remoteView");

  function setLoginUi(active) {
    $("btnLoginStart").classList.toggle("hidden", active);
    $("btnLoginSave").classList.toggle("hidden", !active);
    $("btnLoginStop").classList.toggle("hidden", !active);
    $("remoteWrap").classList.toggle("hidden", !active);
    $("remoteText").classList.toggle("hidden", !active);
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
      endLogin("Sesi login berakhir.");
    } finally { framePending = false; }
  }

  async function pullStatus() {
    try {
      const st = await api("/login/status");
      if (!st.active) return endLogin("Sesi login berakhir.");
      setText("loginState", st.logged_in ? "✅ Login terdeteksi. Klik “Simpan sesi login”." : "Menunggu login…");
    } catch (e) { /* diabaikan */ }
  }

  function endLogin(msg) {
    clearInterval(loginTimer);
    loginTimer = null;
    setLoginUi(false);
    setText("loginState", msg || "");
  }

  $("btnLoginStart").addEventListener("click", async () => {
    $("cookieErr").textContent = "";
    setText("loginState", "Membuka browser…");
    try {
      await api("/login/start", { method: "POST" });
      setLoginUi(true);
      clearInterval(loginTimer);
      let n = 0;
      loginTimer = setInterval(() => { pullFrame(); if (++n % 5 === 0) pullStatus(); }, 700);
      pullFrame();
    } catch (e) { setText("loginState", ""); $("cookieErr").textContent = e.message; }
  });

  $("btnLoginStop").addEventListener("click", async () => {
    await api("/login/stop", { method: "POST" }).catch(() => {});
    endLogin("Dibatalkan.");
  });

  $("btnLoginSave").addEventListener("click", async () => {
    $("cookieErr").textContent = "";
    try {
      const r = await api("/login/save", { method: "POST" });
      renderCookieState(r);
      endLogin(`Berhasil: ${r.saved} cookie tersimpan.`);
      toast("Login tersimpan");
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

  // --------------------------------------------------------------- settings
  const pad = (n) => String(n).padStart(2, "0");
  for (let i = 0; i < 24; i++) $("setScheduleHour").append(new Option(pad(i), pad(i)));
  for (let i = 0; i < 60; i++) $("setScheduleMin").append(new Option(pad(i), pad(i)));

  async function loadSettings() {
    const s = await api("/settings");
    $("setMessage").value = s.message;
    $("setScheduleEnabled").checked = s.schedule_enabled;
    const [hh, mm] = s.schedule_time.split(":");
    $("setScheduleHour").value = hh;
    $("setScheduleMin").value = mm;
    $("setTimezone").value = s.timezone;
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
    setText("dcWebhookState", s.discord_webhook_set ? "(tersimpan)" : "");
    setText("tgTokenState", s.telegram_token_set ? "(tersimpan)" : "");
  }
  $("settingsForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api("/settings", {
        method: "PUT",
        body: {
          message: $("setMessage").value,
          schedule_enabled: $("setScheduleEnabled").checked,
          schedule_time: `${$("setScheduleHour").value}:${$("setScheduleMin").value}`,
          timezone: $("setTimezone").value.trim(),
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
      toast("Pengaturan disimpan");
      refresh();
    } catch (err) { setText("settingsMsg", err.message); }
  });
  $("btnDcTest").addEventListener("click", async () => {
    try { await api("/discord/test", { method: "POST" }); toast("Pesan uji terkirim"); }
    catch (e) { toast(e.message); }
  });
  $("btnTgTest").addEventListener("click", async () => {
    try { await api("/telegram/test", { method: "POST" }); toast("Pesan uji terkirim"); }
    catch (e) { toast(e.message); }
  });

  // ------------------------------------------------------------------ start
  if (apiKey) enter().catch(showLogin); else showLogin();
})();
