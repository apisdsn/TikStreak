"""Otomasi pengiriman pesan streak TikTok lewat browser (DrissionPage)."""
import os
import tempfile
import time

from DrissionPage import ChromiumOptions, ChromiumPage
from DrissionPage.common import Keys

from . import config
from .store import cookies_store

NICKNAME_SELECTORS = [
    'css:p[class*="PInfoNickname"]',
    'css:p[class*="Nickname"]',
    'css:span[class*="Nickname"]',
    'css:div[class*="Nickname"]',
]

INPUT_SELECTORS = [
    'css:div[data-e2e="message-input"]',
    'css:div[contenteditable="true"]',
    'css:textarea[placeholder*="message"]',
    'css:input[placeholder*="message"]',
]

DISMISS_SELECTORS = [
    'xpath://button[contains(., "Maybe later")]',
    'xpath://button[contains(., "Nanti saja")]',
    'css:button.TUXButton--secondary',
    'css:button[class*="TUXButton"][class*="secondary"]',
]


class Cancelled(Exception):
    pass


def xpath_literal(s):
    """Quote string aman untuk XPath."""
    if '"' not in s:
        return f'"{s}"'
    if "'" not in s:
        return f"'{s}'"
    parts = s.split('"')
    return "concat(" + ", '\"', ".join(f'"{p}"' for p in parts) + ")"


class StreakBot:
    def __init__(self, settings, log, cancel_event, test_mode=False, message=None):
        self.s = settings
        self.log = log
        self.cancel = cancel_event
        self.test_mode = test_mode
        self.message = message or settings["message"]
        self.page = None

    # ------------------------------------------------------------------ utils
    def _check_cancel(self):
        if self.cancel.is_set():
            raise Cancelled()

    def _sleep(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            self._check_cancel()
            time.sleep(min(0.25, max(0, end - time.time())))

    # ---------------------------------------------------------------- browser
    def _create_browser(self):
        if not os.path.exists(config.BROWSER_PATH):
            raise RuntimeError(f"Browser tidak ditemukan di {config.BROWSER_PATH}")
        opts = ChromiumOptions()
        opts.set_browser_path(config.BROWSER_PATH)
        opts.set_user_data_path(tempfile.mkdtemp(prefix="chromium-"))
        opts.auto_port()
        for arg in (
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--window-size=1366,900",
            "--lang=en-US",
        ):
            opts.set_argument(arg)
        if config.HEADLESS:
            opts.set_argument("--headless=new")
        opts.set_user_agent(config.USER_AGENT)
        self.page = ChromiumPage(opts)
        self.log("Browser siap")

    def _load_cookies(self):
        cookies = cookies_store.read()
        if not cookies:
            raise RuntimeError("Cookie TikTok belum diatur")
        self.page.get(config.TIKTOK_URL)
        self._sleep(2)
        for c in cookies:
            try:
                self.page.set.cookies(c)
            except Exception as e:  # noqa: BLE001
                self.log(f"Cookie dilewati ({c.get('name')}): {e}", "debug")
        self.log(f"{len(cookies)} cookie dimuat")

    def _verify_login(self):
        self.page.get(config.TIKTOK_MESSAGES_URL)
        self._sleep(self.s["page_load_wait"])
        url = self.page.url or ""
        if "login" in url:
            raise RuntimeError("Belum login, cookie kedaluwarsa atau tidak valid")
        if "messages" not in url:
            raise RuntimeError(f"URL tidak terduga: {url}")
        self.log("Login terverifikasi")
        self._dismiss_popups()

    def _dismiss_popups(self):
        self._sleep(2)
        try:
            dialog = self.page.ele('css:div[role="dialog"], div[class*="TUXModal"]', timeout=2)
        except Exception:  # noqa: BLE001
            dialog = None
        if not dialog:
            return
        for sel in DISMISS_SELECTORS:
            try:
                btn = self.page.ele(sel, timeout=1)
                if btn:
                    btn.click()
                    self.log("Popup ditutup")
                    self._sleep(1)
                    return
            except Exception:  # noqa: BLE001
                continue
        self.log("Popup terdeteksi tetapi tombol tutup tidak ditemukan", "warning")

    # ---------------------------------------------------------------- contact
    def _find_contact(self, name):
        target = name.strip().lower()
        for sel in NICKNAME_SELECTORS:
            try:
                for el in self.page.eles(sel):
                    if (el.text or "").strip().lower() != target:
                        continue
                    parent = el
                    for _ in range(10):
                        parent = parent.parent()
                        if not parent:
                            break
                        cls = parent.attr("class") or ""
                        if "Item" in cls or "item" in cls or "Container" in cls:
                            return parent
                    return el
            except Exception:  # noqa: BLE001
                continue
        try:
            return self.page.ele(f"xpath://*[text()={xpath_literal(name)}]", timeout=1)
        except Exception:  # noqa: BLE001
            return None

    def _find_input(self):
        for sel in INPUT_SELECTORS:
            try:
                el = self.page.ele(sel, timeout=2)
                if el:
                    return el
            except Exception:  # noqa: BLE001
                continue
        return None

    def _visible_nicknames(self):
        names = []
        for sel in NICKNAME_SELECTORS:
            try:
                for el in self.page.eles(sel)[:15]:
                    t = (el.text or "").strip()
                    if t and t not in names:
                        names.append(t)
            except Exception:  # noqa: BLE001
                continue
        return names

    def _send_to(self, name):
        el = self._find_contact(name)
        if not el:
            self.page.refresh()
            self._sleep(self.s["page_load_wait"])
            el = self._find_contact(name)
        if not el:
            raise RuntimeError("Kontak tidak ditemukan di daftar pesan")

        if self.test_mode:
            return

        try:
            el.click()
        except Exception:  # noqa: BLE001
            self.page.run_js("arguments[0].click();", el)
        self._sleep(self.s["element_wait"])

        box = self._find_input()
        if not box:
            raise RuntimeError("Kolom pesan tidak ditemukan")
        box.click()
        self._sleep(0.5)
        box.input(self.message)
        self._sleep(0.5)

        btn = self.page.ele(
            'css:button[data-e2e="send-button"], button[class*="send"], button[class*="Send"]',
            timeout=1,
        )
        if btn:
            btn.click()
        else:
            box.input(Keys.ENTER)
        self._sleep(self.s["send_delay"])

    # -------------------------------------------------------------------- run
    def run(self, contacts):
        """Return dict hasil: {status, sent, total, results}."""
        results = []
        try:
            if not contacts:
                raise RuntimeError("Daftar kontak kosong")
            self._create_browser()
            self._load_cookies()
            self._verify_login()
            self._sleep(self.s["element_wait"] + 2)

            for name in contacts:
                self._check_cancel()
                ok, err = False, None
                for attempt in range(1, 4):
                    try:
                        self.log(f"{'[TEST] ' if self.test_mode else ''}Memproses {name} (percobaan {attempt}/3)")
                        self._send_to(name)
                        ok = True
                        break
                    except Cancelled:
                        raise
                    except Exception as e:  # noqa: BLE001
                        err = str(e)
                        self.log(f"{name}: {err}", "warning")
                        self._sleep(2)
                if ok:
                    self.log(f"{name}: {'ditemukan' if self.test_mode else 'terkirim'}")
                else:
                    shown = ", ".join(self._visible_nicknames()) or "-"
                    self.log(f"Nickname terlihat di halaman: {shown}", "info")
                results.append({"contact": name, "ok": ok, "error": None if ok else err})
                self._sleep(1)
        finally:
            if self.page:
                try:
                    self.page.quit()
                except Exception:  # noqa: BLE001
                    pass
                self.log("Browser ditutup")

        sent = sum(1 for r in results if r["ok"])
        total = len(contacts)
        status = "success" if sent == total else ("partial" if sent else "failed")
        return {"status": status, "sent": sent, "total": total, "results": results}
