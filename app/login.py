"""Sesi browser remote: login TikTok langsung dari panel.

Browser headless dikendalikan lewat CDP. Panel mengambil screenshot berkala
dan meneruskan klik/ketikan pengguna, lalu menyimpan cookie setelah login.
"""
import base64
import os
import tempfile
import threading
import time

from DrissionPage import ChromiumOptions, ChromiumPage

from . import config
from .cookies import from_browser
from .store import cookies_store

IDLE_TIMEOUT = 600  # detik
KEYS = {
    "Backspace": (8, "Backspace"), "Tab": (9, "Tab"), "Enter": (13, "Enter"),
    "Escape": (27, "Escape"), "ArrowLeft": (37, "ArrowLeft"), "ArrowUp": (38, "ArrowUp"),
    "ArrowRight": (39, "ArrowRight"), "ArrowDown": (40, "ArrowDown"), "Delete": (46, "Delete"),
    "Home": (36, "Home"), "End": (35, "End"),
}


class LoginSession:
    def __init__(self):
        self.page = None
        self.last_used = 0
        self._lock = threading.RLock()
        threading.Thread(target=self._reaper, daemon=True).start()

    @property
    def active(self):
        return self.page is not None

    def start(self):
        with self._lock:
            if self.page:
                self.last_used = time.time()
                return
            if not os.path.exists(config.BROWSER_PATH):
                raise RuntimeError(f"Browser tidak ditemukan di {config.BROWSER_PATH}")
            self.last_used = time.time()
            opts = ChromiumOptions()
            opts.set_browser_path(config.BROWSER_PATH)
            opts.set_user_data_path(tempfile.mkdtemp(prefix="chromium-login-"))
            opts.auto_port()
            for arg in ("--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled", "--lang=en-US",
                        "--window-size=1000,700", "--headless=new"):
                opts.set_argument(arg)
            opts.set_user_agent(config.USER_AGENT)
            self.page = ChromiumPage(opts)
            self.page.run_cdp("Emulation.setDeviceMetricsOverride", width=1000, height=700,
                              deviceScaleFactor=1, mobile=False)
            try:
                self.page.get(config.TIKTOK_URL + "/login", timeout=15)
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

    def _reaper(self):
        while True:
            time.sleep(15)
            with self._lock:
                if self.page and time.time() - self.last_used > IDLE_TIMEOUT:
                    self.stop()

    def frame(self):
        """JPEG bytes dari tampilan saat ini."""
        with self._lock:
            self._need()
            r = self.page.run_cdp("Page.captureScreenshot", format="jpeg", quality=60)
            return base64.b64decode(r["data"])

    def _need(self):
        if not self.page:
            raise RuntimeError("Sesi login belum dimulai")
        self.last_used = time.time()

    def input(self, ev):
        with self._lock:
            self._need()
            t = ev.get("type")
            run = self.page.run_cdp
            x, y = float(ev.get("x", 0)), float(ev.get("y", 0))
            if t == "click":
                for kind in ("mouseMoved", "mousePressed", "mouseReleased"):
                    run("Input.dispatchMouseEvent", type=kind, x=x, y=y, button="left",
                        buttons=1 if kind == "mousePressed" else 0, clickCount=1)
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

    def status(self):
        with self._lock:
            if not self.page:
                return {"active": False}
            try:
                url = self.page.url
                names = {c["name"] for c in self.page.cookies(all_domains=True)}
            except Exception:  # noqa: BLE001
                url, names = "", set()
            return {"active": True, "url": url, "logged_in": "sessionid" in names}

    def save(self):
        """Simpan cookie TikTok dari browser. Return jumlah cookie."""
        with self._lock:
            self._need()
            raw = self.page.cookies(all_domains=True, all_info=True)
            cookies = from_browser(raw)
            if not any(c["name"] == "sessionid" for c in cookies):
                raise RuntimeError("Belum login: cookie sessionid belum ada")
            cookies_store.write(cookies)
            return len(cookies)


login_session = LoginSession()
