"""Otomasi pengiriman pesan streak TikTok lewat browser (DrissionPage)."""
import base64
import json
import os
import re
import tempfile
import time
from datetime import datetime

from DrissionPage import ChromiumOptions, ChromiumPage
from DrissionPage.common import Keys

from . import browser, config
from .cookies import from_browser

SHOT_PATH = os.path.join(config.DATA_DIR, "last_run.jpg")
SHOT_META_PATH = os.path.join(config.DATA_DIR, "last_run.json")

# Selector lama (cadangan bila atribut data-e2e daftar chat berubah)
LEGACY_NICKNAME_SELECTORS = [
    'css:p[class*="PInfoNickname"]',
    'css:p[class*="Nickname"]',
    'css:span[class*="Nickname"]',
]

# Daftar chat memakai virtual scroll: hanya item yang terlihat ada di DOM.
SCAN_JS = """
return [...document.querySelectorAll('[data-e2e="dm-new-conversation-item"]')].map(e => {
  const n = e.querySelector('[data-e2e="dm-new-conversation-nickname"]');
  const t = e.querySelector('[class*="SpanInfoTime"]');
  return { id: e.getAttribute('data-conv-id'), nick: n ? n.innerText.trim() : '', time: t ? t.innerText.trim() : '' };
});
"""

SCROLL_JS = """
const it = document.querySelector('[data-e2e="dm-new-conversation-item"]');
if (!it) return null;
let s = it.parentElement;
while (s && s !== document.body) {
  const o = getComputedStyle(s).overflowY;
  if ((o === 'auto' || o === 'scroll') && s.scrollHeight > s.clientHeight) break;
  s = s.parentElement;
}
if (!s || s === document.body) return null;
if (arguments[0] === 'top') { s.scrollTop = 0; return { top: true }; }
const before = s.scrollTop;
s.scrollTop += Math.max(200, s.clientHeight * 0.8);
return { moved: s.scrollTop !== before, atEnd: s.scrollTop + s.clientHeight >= s.scrollHeight - 2 };
"""

MSG_COUNT_JS = """
const box = document.querySelector('[data-e2e="dm-new-message-list"]') || document.body;
return box.innerText.split(arguments[0]).length - 1;
"""

INPUT_SELECTORS = [
    'css:div[data-e2e="message-input-area"] div[contenteditable="true"]',
    'css:div[data-e2e="message-input"] div[contenteditable="true"]',
    'css:div[data-e2e="message-input"]',
    'css:div[contenteditable="true"]',
    'css:textarea[placeholder*="message"]',
]

HEADER_SELECTORS = [
    'css:p[data-e2e="dm-new-chat-nickname"]',
    'css:[data-e2e="chat-nickname"]',
    'css:[class*="ChatHeader"] [class*="Nickname"]',
    'css:[class*="ChatHeader"] p',
]
HEADER_UID_SELECTOR = 'css:p[data-e2e="chat-uniqueid"]'
MESSAGE_TEXT_SELECTOR = 'css:[data-e2e="dm-new-message-text"]'

TIME_RE = re.compile(r"\s*([01]?\d|2[0-3]):([0-5]\d)\s*")

SEND_BUTTON_SELECTORS = [
    'css:[data-e2e="message-send"]',
    'css:button[data-e2e="send-button"]',
    'css:[class*="SendButton"]',
    'css:svg[class*="Send"]',
]

DISMISS_SELECTORS = [
    'xpath://button[contains(., "Maybe later")]',
    'xpath://button[contains(., "Nanti saja")]',
    'css:button.TUXButton--secondary',
    'css:button[class*="TUXButton"][class*="secondary"]',
]


class Cancelled(Exception):
    pass


class CookieInvalid(RuntimeError):
    """Cookie belum diatur, kedaluwarsa, atau ditolak TikTok."""


def xpath_literal(s):
    """Quote string aman untuk XPath."""
    if '"' not in s:
        return f'"{s}"'
    if "'" not in s:
        return f"'{s}'"
    parts = s.split('"')
    return "concat(" + ", '\"', ".join(f'"{p}"' for p in parts) + ")"


class StreakBot:
    def __init__(self, settings, log, cancel_event, cookies_store, test_mode=False, message=None, check_only=False, proof_dir=None, convs_store=None, account_id=None, provider=None, message_fn=None):
        self.s = settings
        self.cookies_store = cookies_store
        self.log = log
        self.cancel = cancel_event
        self.test_mode = test_mode
        self.message = message or settings["message"]
        self.message_fn = message_fn  # nama kontak -> teks (variasi, placeholder); None = satu pesan untuk semua
        self.check_only = check_only
        self.proof_dir = proof_dir
        self.convs = convs_store
        self.account_id = account_id
        self.provider = provider  # pemberi tab di konteks terisolasi (pool); None = browser sendiri
        self.page = None
        self.logged_in = False
        self.cookies_saved = False

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
        if self.provider:
            self.page = self.provider.acquire(block_media=True)
            self.log("Browser Siap")
            return
        if not os.path.exists(config.BROWSER_PATH):
            raise RuntimeError(f"Browser Tidak Ditemukan di {config.BROWSER_PATH}")
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
        opts.set_user_agent(browser.build_ua())
        self.page = ChromiumPage(opts)
        browser.apply_fingerprint(self.page)
        self.log("Browser Siap")

    def _cookies(self, all_info=False):
        """Cookie browser. Di konteks terisolasi (pool) hanya Network.getAllCookies yang tersaring per konteks."""
        if self.provider:
            raw = self.page.run_cdp("Network.getAllCookies")["cookies"]
            return raw if all_info else [{"name": c["name"], "value": c["value"], "domain": c["domain"]} for c in raw]
        return self.page.cookies(all_domains=True, all_info=all_info)

    def _load_cookies(self):
        cookies = self.cookies_store.read()
        if not cookies:
            raise CookieInvalid("Cookie TikTok Belum Diatur")
        self.page.get(config.TIKTOK_URL)
        self._sleep(2)
        for c in cookies:
            try:
                self.page.set.cookies(c)
            except Exception as e:  # noqa: BLE001
                self.log(f"Cookie Dilewati ({c.get('name')}): {e}", "debug")
        self.log(f"{len(cookies)} Cookie Dimuat")

    def _verify_login(self):
        self.page.get(config.TIKTOK_MESSAGES_URL)
        self._sleep(self.s["page_load_wait"])
        url = self.page.url or ""
        if "login" in url:
            raise CookieInvalid("Cookie Kedaluwarsa atau Tidak Valid (Diarahkan ke Halaman Login)")
        if "messages" not in url:
            raise RuntimeError(f"URL Tidak Terduga: {url}")
        names = {c.get("name") for c in self._cookies()}
        if "sessionid" not in names:
            raise CookieInvalid("Cookie sessionid Ditolak TikTok (Sesi Sudah Tidak Berlaku)")
        try:
            login_btn = self.page.ele('css:[data-e2e="top-login-button"]', timeout=1)
        except Exception:  # noqa: BLE001
            login_btn = None
        if login_btn:
            raise CookieInvalid("TikTok Menampilkan Tombol Log In (Sesi Tidak Berlaku)")
        self.logged_in = True
        self.log("Login Terverifikasi")
        self._save_cookies()
        self._dismiss_popups()

    def _save_cookies(self):
        """Simpan cookie terbaru dari browser (TikTok memperbarui sesi saat dipakai)."""
        try:
            fresh = from_browser(self._cookies(all_info=True))
            if any(c["name"] == "sessionid" for c in fresh):
                self.cookies_store.write(fresh)
                self.cookies_saved = True
                self.log(f"Cookie Diperbarui ({len(fresh)})")
        except Exception as e:  # noqa: BLE001
            self.log(f"Gagal Menyimpan Cookie Terbaru: {e}", "warning")

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
                    self.log("Popup Ditutup")
                    self._sleep(1)
                    return
            except Exception:  # noqa: BLE001
                continue
        self.log("Popup Terdeteksi Tetapi Tombol Tutup Tidak Ditemukan", "warning")

    # ---------------------------------------------------------------- contact
    def _find_contact_legacy(self, name):
        target = name.strip().lower()
        for sel in LEGACY_NICKNAME_SELECTORS:
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
        return None

    def _scroll_list(self, where):
        try:
            return self.page.run_js(SCROLL_JS, where)
        except Exception:  # noqa: BLE001
            return None

    def _scan(self):
        try:
            return self.page.run_js(SCAN_JS) or []
        except Exception:  # noqa: BLE001
            return []

    def _locate(self, name, conv_id=None):
        """Cari kartu kontak di daftar chat (menggulir daftar virtual).

        Prioritas: ID percakapan yang pernah tersimpan (tahan terhadap perubahan nama),
        lalu nama persis. Return dict {el, nick, id, time} atau None.
        """
        target = name.strip().lower()
        phases = (["id"] if conv_id else []) + ["name"]
        for phase in phases:
            self._scroll_list("top")
            self._sleep(0.3)
            for step in range(80):
                self._check_cancel()
                items = self._scan()
                if not items and step == 0 and phase == phases[0]:
                    el = self._find_contact_legacy(name)
                    return {"el": el, "nick": name, "id": None, "time": None} if el else None
                if phase == "id":
                    hit = next((i for i in items if i["id"] == conv_id), None)
                else:
                    hit = next((i for i in items if i["nick"].strip().lower() == target), None)
                if hit:
                    el = self.page.ele(f'css:div[data-conv-id="{hit["id"]}"]', timeout=2)
                    if el:
                        return {"el": el, **hit}
                r = self._scroll_list("down")
                if not r or r.get("atEnd") or not r.get("moved"):
                    # satu pemindaian terakhir di dasar daftar
                    items = self._scan()
                    hit = next((i for i in items if (i["id"] == conv_id if phase == "id" else i["nick"].strip().lower() == target)), None)
                    if hit:
                        el = self.page.ele(f'css:div[data-conv-id="{hit["id"]}"]', timeout=2)
                        if el:
                            return {"el": el, **hit}
                    break
                self._sleep(0.3)
        return None

    def _remember(self, name, conv_id):
        """Simpan ID percakapan untuk kontak ini agar tetap dikenali bila namanya berubah."""
        if not self.convs or not conv_id:
            return
        key = name.strip().lower()
        data = self.convs.read()
        if data.get(key) != conv_id:
            data[key] = conv_id
            self.convs.write(data)

    def _find_input(self):
        for sel in INPUT_SELECTORS:
            try:
                els = self.page.eles(sel, timeout=2)
                if els:
                    return els[-1]  # kotak chat berada paling bawah
            except Exception:  # noqa: BLE001
                continue
        return None

    def _input_text(self):
        box = self._find_input()
        return (box.text or "").strip() if box else ""

    def _count_text(self, text):
        try:
            return self.page.run_js(MSG_COUNT_JS, text)
        except Exception:  # noqa: BLE001
            return 0

    def _clear_input(self):
        run = self.page.run_cdp
        run("Input.dispatchKeyEvent", type="keyDown", key="a", code="KeyA",
            windowsVirtualKeyCode=65, modifiers=2, commands=["selectAll"])
        run("Input.dispatchKeyEvent", type="keyUp", key="a", code="KeyA", windowsVirtualKeyCode=65)
        run("Input.dispatchKeyEvent", type="keyDown", key="Backspace", code="Backspace",
            windowsVirtualKeyCode=8)
        run("Input.dispatchKeyEvent", type="keyUp", key="Backspace", code="Backspace",
            windowsVirtualKeyCode=8)
        self._sleep(0.3)

    def _press_enter(self):
        run = self.page.run_cdp
        run("Input.dispatchKeyEvent", type="keyDown", key="Enter", code="Enter",
            windowsVirtualKeyCode=13, text="\r")
        run("Input.dispatchKeyEvent", type="keyUp", key="Enter", code="Enter",
            windowsVirtualKeyCode=13)

    def _click_send_button(self):
        for sel in SEND_BUTTON_SELECTORS:
            try:
                btn = self.page.ele(sel, timeout=1)
                if btn:
                    try:
                        btn.click()
                    except Exception:  # noqa: BLE001
                        self.page.run_js("arguments[0].click();", btn)
                    return True
            except Exception:  # noqa: BLE001
                continue
        return False

    def _wait_sent(self, before, timeout=6):
        """Terkirim bila kotak input kosong dan teks muncul sebagai bubble baru."""
        end = time.time() + timeout
        while time.time() < end:
            self._sleep(0.5)
            if not self._input_text() and self._count_text(self.message) > before:
                return True
        return False

    def _chat_header(self):
        """(nama, @username) pada header chat yang terbuka; elemen yang tak terbaca bernilai None."""
        nick = uid = None
        for sel in HEADER_SELECTORS:
            try:
                for el in self.page.eles(sel, timeout=1):
                    t = (el.text or "").strip()
                    if t:
                        nick = t
                        break
            except Exception:  # noqa: BLE001
                continue
            if nick:
                break
        try:
            el = self.page.ele(HEADER_UID_SELECTOR, timeout=0.5)
            uid = (el.text or "").strip() if el else None
        except Exception:  # noqa: BLE001
            uid = None
        return nick, uid or None

    def _list_time(self, name, conv_id=None):
        """Jam pesan terakhir pada kartu kontak di daftar chat (HH:MM) atau None."""
        found = self._locate(name, conv_id)
        if not found or not found.get("time"):
            return None
        m = TIME_RE.fullmatch(found["time"])
        return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None

    def _last_bubble(self):
        try:
            els = self.page.eles(MESSAGE_TEXT_SELECTOR, timeout=1)
            if els:
                return (els[-1].text or "").strip()
            els = self.page.eles(f"xpath://*[normalize-space(text())={xpath_literal(self.message)}]", timeout=1)
            return (els[-1].text or "").strip() if els else None
        except Exception:  # noqa: BLE001
            return None

    def _capture_proof(self, index):
        """Screenshot chat setelah pesan terverifikasi terkirim. Return nama file."""
        if not self.proof_dir or self.test_mode or not self.s.get("notify_screenshot"):
            return None
        try:
            os.makedirs(self.proof_dir, exist_ok=True)
            r = self.page.run_cdp("Page.captureScreenshot", format="jpeg", quality=60)
            name = f"{index}.jpg"
            with open(os.path.join(self.proof_dir, name), "wb") as f:
                f.write(base64.b64decode(r["data"]))
            return name
        except Exception:  # noqa: BLE001
            return None

    def _snapshot(self):
        try:
            r = self.page.run_cdp("Page.captureScreenshot", format="jpeg", quality=70)
            with open(SHOT_PATH, "wb") as f:
                f.write(base64.b64decode(r["data"]))
            with open(SHOT_META_PATH, "w", encoding="utf-8") as f:
                json.dump({"account_id": self.account_id}, f)
        except Exception:  # noqa: BLE001
            pass

    def _visible_nicknames(self):
        names = [i["nick"] for i in self._scan() if i["nick"]]
        if names:
            return names[:15]
        for sel in LEGACY_NICKNAME_SELECTORS:
            try:
                names += [(el.text or "").strip() for el in self.page.eles(sel)[:15]]
            except Exception:  # noqa: BLE001
                continue
        return [n for n in dict.fromkeys(names) if n][:15]

    def scan_contacts(self, limit=200):
        """Kumpulkan percakapan dari daftar chat (menggulir daftar virtual). Return [{id, nick, time}] maksimal limit."""
        found = {}

        def collect():
            for i in self._scan():
                if i.get("id") and i.get("nick") and i["id"] not in found:
                    found[i["id"]] = {"id": i["id"], "nick": i["nick"], "time": i.get("time") or ""}

        try:
            self._create_browser()
            self._load_cookies()
            self._verify_login()
            self._sleep(self.s["element_wait"] + 2)
            self._scroll_list("top")
            self._sleep(0.3)
            for _ in range(400):
                self._check_cancel()
                collect()
                if len(found) >= limit:
                    break
                r = self._scroll_list("down")
                if not r or r.get("atEnd") or not r.get("moved"):
                    self._sleep(0.3)
                    collect()
                    break
                self._sleep(0.3)
        finally:
            if self.page:
                try:
                    if self.provider:
                        self.provider.release(self.page)
                    else:
                        self.page.quit()
                except Exception:  # noqa: BLE001
                    pass
        return list(found.values())[:limit]

    def _send_to(self, name):
        """Kirim ke satu kontak. Return dict bukti (chat, bubble, count, list_time, renamed_to)."""
        conv_id = self.convs.read().get(name.strip().lower()) if self.convs else None
        found = self._locate(name, conv_id)
        if not found:
            self.page.refresh()
            self._sleep(self.s["page_load_wait"])
            found = self._locate(name, conv_id)
        if not found:
            raise RuntimeError("Kontak Tidak Ditemukan di Daftar Pesan")

        el, nick, cid = found["el"], found["nick"], found.get("id")
        evidence = {}
        if nick.strip().lower() != name.strip().lower():
            evidence["renamed_to"] = nick
            self.log(f"{name}: Nama Berubah Menjadi '{nick}' (Dikenali lewat ID Percakapan)", "warning")
        self._remember(name, cid)
        if self.test_mode:
            return evidence

        try:
            el.click()
        except Exception:  # noqa: BLE001
            self.page.run_js("arguments[0].click();", el)
        self._sleep(self.s["element_wait"])

        # Pastikan chat yang terbuka memang milik penerima
        header, uid = self._chat_header()
        if header is not None and nick.strip().lower() not in header.lower():
            raise RuntimeError(f"Chat yang Terbuka Milik '{header}', Bukan '{nick}'. Pesan Tidak Dikirim")
        if header is None:
            self.log("Header Chat Tidak Terbaca, Penerima Tidak Bisa Diverifikasi", "warning")
        evidence["chat"] = header
        if uid:
            evidence["uid"] = uid

        box = self._find_input()
        if not box:
            raise RuntimeError("Kolom Pesan Tidak Ditemukan")
        before = self._count_text(self.message)
        box.click()
        self._sleep(0.5)
        if self._input_text():
            self._clear_input()
        self.page.run_cdp("Input.insertText", text=self.message)
        self._sleep(0.7)
        if self._input_text() == "":
            raise RuntimeError("Teks Tidak Masuk ke Kolom Pesan")

        self._press_enter()
        sent = self._wait_sent(before)
        if not sent and self._click_send_button():
            sent = self._wait_sent(before)
        if not sent:
            raise RuntimeError("Pesan Tidak Terverifikasi Terkirim (Cek Screenshot)")

        evidence["bubble"] = self._last_bubble()
        evidence["count"] = [before, self._count_text(self.message)]
        self._sleep(2)  # beri waktu daftar chat memperbarui pratinjau
        evidence["list_time"] = self._list_time(nick, cid)
        return evidence

    # -------------------------------------------------------------------- run
    def run(self, contacts):
        """Return dict hasil: {status, sent, total, results}."""
        results = []
        try:
            if not contacts and not self.check_only:
                raise RuntimeError("Daftar Kontak Kosong")
            self._create_browser()
            self._load_cookies()
            self._verify_login()
            if self.check_only:
                return {"status": "success", "sent": 0, "total": 0, "results": []}
            self._sleep(self.s["element_wait"] + 2)

            for name in contacts:
                self._check_cancel()
                if self.message_fn:
                    self.message = self.message_fn(name)
                ok, err, evidence = False, None, None
                for attempt in range(1, 4):
                    try:
                        self.log(f"{'[TEST] ' if self.test_mode else ''}Memproses {name} (Percobaan {attempt}/3)")
                        evidence = self._send_to(name)
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
                    self.log(f"Nickname Terlihat di Halaman: {shown}", "info")
                results.append({
                    "contact": name, "ok": ok, "error": None if ok else err, "message": self.message,
                    "sent_at": datetime.now().strftime("%H:%M:%S") if ok and not self.test_mode else None,
                    "proof": self._capture_proof(len(results)) if ok else None,
                    "evidence": evidence if ok else None,
                })
                self._sleep(1)
        finally:
            if self.page:
                self._snapshot()
                if self.logged_in and not self.check_only:
                    self._save_cookies()
                try:
                    if self.provider:
                        self.provider.release(self.page)
                    else:
                        self.page.quit()
                except Exception:  # noqa: BLE001
                    pass
                self.log("Browser Ditutup")

        sent = sum(1 for r in results if r["ok"])
        total = len(contacts)
        status = "success" if sent == total else ("partial" if sent else "failed")
        return {"status": status, "sent": sent, "total": total, "results": results}
