"""Sesi browser remote: login TikTok langsung dari panel.

Browser headless dikendalikan lewat CDP. Panel mengambil screenshot berkala
dan meneruskan klik/ketikan pengguna, lalu menyimpan cookie setelah login.
Tab/popup baru diikuti otomatis, dialog JS ditutup otomatis, dan beberapa
catatan diagnostik (tanpa cookie/teks ketikan) disimpan untuk membantu analisis.
"""
import base64
import os
import re
import tempfile
import threading
import time
from collections import OrderedDict, deque
from urllib.parse import urlparse

from DrissionPage import ChromiumOptions, ChromiumPage

from . import browser, config
from .cookies import from_browser
from .store import stores

IDLE_TIMEOUT = 600  # detik
VIEW_W, VIEW_H = 1000, 700
KEYS = {
    "Backspace": (8, "Backspace"), "Tab": (9, "Tab"), "Enter": (13, "Enter"),
    "Escape": (27, "Escape"), "ArrowLeft": (37, "ArrowLeft"), "ArrowUp": (38, "ArrowUp"),
    "ArrowRight": (39, "ArrowRight"), "ArrowDown": (40, "ArrowDown"), "Delete": (46, "Delete"),
    "Home": (36, "Home"), "End": (35, "End"),
}
_TOKEN = re.compile(r"[A-Za-z0-9_\-%.]{24,}")


def _clean(text, limit=160):
    """Potong dan samarkan string panjang mirip token agar tidak membocorkan rahasia."""
    return _TOKEN.sub("…", str(text or "").replace("\n", " "))[:limit]


def _path_of(url):
    """host + path saja (tanpa query/fragment)."""
    try:
        u = urlparse(url)
        return (u.netloc + u.path)[:140]
    except Exception:  # noqa: BLE001
        return ""


class LoginSession:
    def __init__(self):
        self.page = None
        self.account_id = None
        self.owner_id = None
        self.last_used = 0
        self._lock = threading.RLock()
        self._tabs = {}          # id tab -> objek tab
        self._order = []         # urutan tab dibuka
        self.active_id = None
        self.diag = deque(maxlen=20)
        self._reqs = OrderedDict()

    @property
    def active(self):
        return self.page is not None

    # ------------------------------------------------------------ diagnostik
    def _add(self, kind, msg):
        self.diag.append({"t": time.strftime("%H:%M:%S"), "kind": kind, "msg": msg})

    def _login_url(self):
        return config.LOGIN_START_URL or config.TIKTOK_URL + "/login"

    def _hook(self, tab, tid):
        """Pasang pendengar peristiwa untuk satu tab (dialog, error konsol, jaringan)."""
        drv = tab.driver

        def on_dialog(**kw):
            self._add("dialog", f"{str(kw.get('type', 'dialog')).capitalize()} Ditutup Otomatis: {_clean(kw.get('message'), 120)}")
            try:
                tab._on_alert_open(**kw)  # penanganan bawaan (auto accept)
            except Exception:  # noqa: BLE001
                pass

        def on_exc(**kw):
            d = kw.get("exceptionDetails") or {}
            self._add("console", f"Error JS: {_clean(d.get('text'), 80)} {_path_of(d.get('url', ''))}".strip())

        def on_console(**kw):
            if kw.get("type") != "error":
                return
            args = kw.get("args") or []
            first = args[0].get("value", args[0].get("description", "")) if args else ""
            self._add("console", f"Console Error: {_clean(first, 120)}")

        def on_req(**kw):
            self._reqs[kw.get("requestId")] = _path_of((kw.get("request") or {}).get("url", ""))
            while len(self._reqs) > 300:
                self._reqs.popitem(last=False)

        def on_failed(**kw):
            if kw.get("canceled") or kw.get("errorText") == "net::ERR_ABORTED":
                return
            self._add("network", f"Gagal Dimuat: {self._reqs.get(kw.get('requestId'), '?')} ({kw.get('errorText', '')})")

        def on_resp(**kw):
            r = kw.get("response") or {}
            path = _path_of(r.get("url", ""))
            if r.get("status", 0) >= 400 and ("tiktok" in path.split("/")[0] or self._is_test_host(path)):
                self._add("network", f"HTTP {r.get('status')} {path}")

        for name in ("Page.enable", "Runtime.enable", "Network.enable"):
            try:
                tab.run_cdp(name)
            except Exception:  # noqa: BLE001
                pass
        try:
            tab.set.auto_handle_alert(True, accept=True)
        except Exception:  # noqa: BLE001
            pass
        for ev, fn, imm in (("Page.javascriptDialogOpening", on_dialog, True), ("Runtime.exceptionThrown", on_exc, False),
                            ("Runtime.consoleAPICalled", on_console, False), ("Network.requestWillBeSent", on_req, False),
                            ("Network.loadingFailed", on_failed, False), ("Network.responseReceived", on_resp, False)):
            try:
                drv.set_callback(ev, fn, immediate=imm)
            except Exception:  # noqa: BLE001
                pass

    @staticmethod
    def _is_test_host(path):
        return bool(config.LOGIN_START_URL) and path.split("/")[0] == urlparse(config.LOGIN_START_URL).netloc

    def _setup_tab(self, tab, tid):
        browser.apply_fingerprint(tab)
        try:
            tab.run_cdp("Emulation.setDeviceMetricsOverride", width=VIEW_W, height=VIEW_H, deviceScaleFactor=1, mobile=False)
        except Exception:  # noqa: BLE001
            pass
        self._hook(tab, tid)

    # ------------------------------------------------------------------ tab
    def _sync(self):
        """Ikuti tab baru (jadi aktif) dan pulihkan bila tab aktif tertutup."""
        if not self.page:
            return
        try:
            ids = list(self.page.browser.tab_ids)
        except Exception:  # noqa: BLE001
            return
        alive = set(ids)
        for tid in list(self._tabs):
            if tid not in alive:
                self._tabs.pop(tid, None)
                if tid in self._order:
                    self._order.remove(tid)
                self._add("tab", "Tab Ditutup")
        new = []
        for tid in reversed(ids):  # dari yang tertua ke terbaru
            if tid in self._tabs:
                continue
            try:
                tab = self.page.get_tab(tid)
            except Exception:  # noqa: BLE001
                continue  # belum siap; dicoba lagi pada sinkronisasi berikutnya
            self._tabs[tid] = tab
            self._order.append(tid)
            self._setup_tab(tab, tid)
            new.append(tid)
        if new:
            self._activate(new[-1])
            self._add("tab", f"Tab Baru Dibuka ({len(self._order)} Tab)")
        elif self.active_id not in self._tabs and self._order:
            self._activate(self._order[-1])

    def _activate(self, tid):
        self.active_id = tid
        try:
            self.page.activate_tab(tid)
        except Exception:  # noqa: BLE001
            pass

    def _tab(self):
        self._sync()
        tab = self._tabs.get(self.active_id)
        if tab is None:
            raise RuntimeError("Sesi Login Belum Dimulai")
        return tab

    # ---------------------------------------------------------------- hidup
    def start(self, account_id):
        with self._lock:
            if self.page:
                if self.account_id != account_id:
                    raise RuntimeError("Sesi Login untuk Akun Lain Masih Terbuka. Batalkan Dulu.")
                self.last_used = time.time()
                return
            self.account_id = account_id
            if not os.path.exists(config.BROWSER_PATH):
                raise RuntimeError(f"Browser Tidak Ditemukan di {config.BROWSER_PATH}")
            self.last_used = time.time()
            opts = ChromiumOptions()
            opts.set_browser_path(config.BROWSER_PATH)
            opts.set_user_data_path(tempfile.mkdtemp(prefix="chromium-login-"))
            opts.auto_port()
            for arg in ("--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled", "--lang=en-US",
                        f"--window-size={VIEW_W},{VIEW_H}", "--headless=new"):
                opts.set_argument(arg)
            opts.set_user_agent(browser.build_ua())
            self.page = ChromiumPage(opts)
            self._tabs, self._order, self.diag = {}, [], deque(maxlen=20)
            main = self.page.tab_id
            self._tabs[main] = self.page
            self._order.append(main)
            self.active_id = main
            self._setup_tab(self.page, main)
            try:
                self.page.run_cdp("Page.navigate", url=self._login_url())
            except Exception:  # noqa: BLE001
                pass  # tampilan tetap bisa dipakai; pengguna dapat memuat ulang
            self.last_used = time.time()

    def stop(self):
        with self._lock:
            if self.page:
                try:
                    self.page.quit()
                except Exception:  # noqa: BLE001
                    pass
                self.page = None
                self.account_id = None
                self._tabs, self._order, self.active_id = {}, [], None

    def idle_expired(self):
        return bool(self.page) and time.time() - self.last_used > IDLE_TIMEOUT

    def _need(self):
        if not self.page:
            raise RuntimeError("Sesi Login Belum Dimulai")
        self.last_used = time.time()

    def frame(self):
        """JPEG bytes dari tab aktif."""
        with self._lock:
            self._need()
            last = None
            for _ in range(3):  # saat navigasi, tangkapan layar bisa gagal sesaat
                try:
                    r = self._tab().run_cdp("Page.captureScreenshot", format="jpeg", quality=60)
                    return base64.b64decode(r["data"])
                except Exception as e:  # noqa: BLE001
                    last = e
                    time.sleep(0.25)
            raise last

    # ---------------------------------------------------------------- input
    def input(self, ev):
        with self._lock:
            self._need()
            t = ev.get("type")
            tab = self._tab()
            run = tab.run_cdp
            x, y = float(ev.get("x", 0)), float(ev.get("y", 0))
            mouse = {"pointerType": "mouse", "button": "left"}
            if t == "click":
                # gerakkan pointer, tahan sebentar, lalu lepas agar komponen yang butuh hover/pointerdown bereaksi
                run("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y, button="none", buttons=0, pointerType="mouse")
                time.sleep(0.04)
                run("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, buttons=1, clickCount=1, **mouse)
                time.sleep(0.07)
                run("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, buttons=0, clickCount=1, **mouse)
            elif t == "move":
                run("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y, button="none", buttons=0, pointerType="mouse")
            elif t == "scroll":
                run("Input.dispatchMouseEvent", type="mouseWheel", x=x, y=y,
                    deltaX=float(ev.get("dx", 0)), deltaY=float(ev.get("dy", 0)))
            elif t == "text":
                run("Input.insertText", text=str(ev.get("text", ""))[:500])
            elif t == "key":
                key = ev.get("key", "")
                if key in KEYS:
                    code, name = KEYS[key]
                    extra = {"text": "\r"} if key == "Enter" else {}
                    run("Input.dispatchKeyEvent", type="keyDown" if extra else "rawKeyDown",
                        key=name, code=name, windowsVirtualKeyCode=code, **extra)
                    run("Input.dispatchKeyEvent", type="keyUp", key=name, code=name,
                        windowsVirtualKeyCode=code)
                elif len(key) == 1:
                    run("Input.insertText", text=key)
            elif t == "nav":
                self._nav(tab, ev)

    def _nav(self, tab, ev):
        a = ev.get("action")
        if a == "reload":
            tab.run_cdp("Page.reload")
        elif a == "back":
            h = tab.run_cdp("Page.getNavigationHistory")
            i = h.get("currentIndex", 0)
            if i > 0:
                tab.run_cdp("Page.navigateToHistoryEntry", entryId=h["entries"][i - 1]["id"])
        elif a == "login":
            tab.run_cdp("Page.navigate", url=self._login_url())
        elif a == "tab" and len(self._order) > 1:
            idx = int(ev.get("index", 0))
            cur = self._order.index(self.active_id)
            target = self._order[(idx - 1) % len(self._order)] if idx > 0 else self._order[(cur + 1) % len(self._order)]
            self._activate(target)

    # --------------------------------------------------------------- status
    def status(self):
        with self._lock:
            if not self.page:
                return {"active": False}
            try:
                tab = self._tab()
                url = _path_of(tab.url)
                names = {c["name"] for c in tab.cookies(all_domains=True)}
            except Exception:  # noqa: BLE001
                url, names = "", set()
            n = len(self._order)
            idx = self._order.index(self.active_id) + 1 if self.active_id in self._order else 1
            return {"active": True, "account": self.account_id, "url": url, "logged_in": "sessionid" in names,
                    "tabs": n, "tab": idx, "diag": list(self.diag)}

    def save(self):
        """Simpan cookie TikTok dari browser. Return jumlah cookie."""
        with self._lock:
            self._need()
            raw = self._tab().cookies(all_domains=True, all_info=True)
            cookies = from_browser(raw)
            if not any(c["name"] == "sessionid" for c in cookies):
                raise RuntimeError("Belum Login: Cookie sessionid Belum Ada")
            stores(self.account_id).cookies.write(cookies)
            return len(cookies)


class LoginManager:
    """Sesi login remote: satu per pengguna, dibatasi LOGIN_SESSIONS di seluruh panel."""

    def __init__(self):
        self._sessions = {}
        self._lock = threading.RLock()
        self._thread = None

    def _ensure_reaper(self):
        if self._thread:
            return
        self._thread = threading.Thread(target=self._reaper, daemon=True, name="bara-login-reaper")
        self._thread.start()

    def _reaper(self):
        while True:
            time.sleep(15)
            with self._lock:
                for uid, s in list(self._sessions.items()):
                    if s.idle_expired():
                        s.stop()
                    if not s.active:
                        self._sessions.pop(uid, None)

    def session_for(self, owner_id):
        """Sesi milik pengguna; bila belum ada, objek tidak aktif (semua operasinya gagal dengan pesan wajar)."""
        with self._lock:
            return self._sessions.get(owner_id) or LoginSession()

    def start(self, owner_id, account_id):
        with self._lock:
            self._ensure_reaper()
            s = self._sessions.get(owner_id)
            if s and s.active:
                s.start(account_id)
                return s
            busy = [x for x in self._sessions.values() if x.active]
            if len(busy) >= config.LOGIN_SESSIONS:
                raise RuntimeError("Browser Login Sedang Dipakai, Coba Lagi Sebentar")
            s = LoginSession()
            s.owner_id = owner_id
            s.start(account_id)
            self._sessions[owner_id] = s
            return s

    def active_account_ids(self):
        with self._lock:
            return {s.account_id for s in self._sessions.values() if s.active}

    def account_active(self, account_id):
        return account_id in self.active_account_ids()

    def stop_owner(self, owner_id):
        with self._lock:
            s = self._sessions.pop(owner_id, None)
        if s:
            s.stop()

    def stop_account(self, account_id):
        with self._lock:
            for uid, s in list(self._sessions.items()):
                if s.active and s.account_id == account_id:
                    s.stop()
                    self._sessions.pop(uid, None)

    def count(self):
        with self._lock:
            return sum(1 for s in self._sessions.values() if s.active)


login_mgr = LoginManager()
