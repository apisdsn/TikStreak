"""Menjalankan bot di thread, menyimpan log live + riwayat, dan scheduler harian."""
import threading
import time
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import config
from .bot import Cancelled, CookieInvalid, StreakBot
from .login import login_session
from .notify import notify
from .store import contacts_store, cookies_store, get_settings, history_store, meta_store

MAX_HISTORY = 50
MAX_LOG_LINES = 500
ALERT_COOLDOWN = 6 * 3600  # jeda minimal antar alert cookie dari cek otomatis


class Busy(Exception):
    pass


def _tz(settings):
    try:
        return ZoneInfo(settings.get("timezone") or config.DEFAULT_TZ)
    except Exception:  # noqa: BLE001
        return ZoneInfo("UTC")


class Runner:
    def __init__(self):
        self._lock = threading.Lock()
        self.current = None
        self._cancel = threading.Event()
        self._last_fire_key = None

    # ------------------------------------------------------------- run control
    def start(self, mode="send", message=None, trigger="manual"):
        with self._lock:
            if self.current and self.current["status"] == "running":
                raise Busy()
            run = {
                "id": uuid.uuid4().hex[:8],
                "mode": mode,
                "trigger": trigger,
                "status": "running",
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "finished_at": None,
                "sent": 0,
                "total": 0,
                "results": [],
                "logs": [],
            }
            self.current = run
            self._cancel.clear()
        threading.Thread(target=self._execute, args=(run, message), daemon=True).start()
        return run

    def stop(self):
        self._cancel.set()

    def _log_fn(self, run):
        def log(msg, level="info"):
            line = {"t": datetime.now().strftime("%H:%M:%S"), "level": level, "msg": msg}
            run["logs"].append(line)
            if len(run["logs"]) > MAX_LOG_LINES:
                del run["logs"][: len(run["logs"]) - MAX_LOG_LINES]
        return log

    def _execute(self, run, message):
        settings = get_settings()
        log = self._log_fn(run)
        mode = run["mode"]
        log({"test": "Mode uji (tidak mengirim pesan)", "check": "Cek & perbarui cookie"}.get(mode, "Mulai mengirim streak"))
        bot = None
        try:
            contacts = contacts_store.read()
            bot = StreakBot(settings, log, self._cancel, test_mode=(mode == "test"),
                            message=message, check_only=(mode == "check"))
            res = bot.run(contacts)
            run.update(res)
            log("Cookie valid" if mode == "check" else f"Selesai: {res['sent']}/{res['total']}")
        except Cancelled:
            run["status"] = "cancelled"
            log("Dihentikan oleh pengguna", "warning")
        except CookieInvalid as e:
            run["status"] = "failed"
            run["error"] = str(e)
            run["cookie_invalid"] = True
            log(f"Gagal: {e}", "error")
        except Exception as e:  # noqa: BLE001
            run["status"] = "failed"
            run["error"] = str(e)
            log(f"Gagal: {e}", "error")
        self._update_meta(run, bot)
        run["finished_at"] = datetime.now().isoformat(timespec="seconds")
        self._save_history(run)
        self._notify(settings, run)

    def _update_meta(self, run, bot):
        meta = meta_store.read()
        now = datetime.now().isoformat(timespec="seconds")
        if bot and bot.logged_in:
            meta["last_ok"] = now
            meta.pop("invalid", None)
        if bot and bot.cookies_saved:
            meta["last_saved"] = now
        if run.get("cookie_invalid"):
            meta["invalid"] = run["error"]
        meta_store.write(meta)

    def _save_history(self, run):
        hist = history_store.read()
        hist.insert(0, {k: v for k, v in run.items()})
        history_store.write(hist[:MAX_HISTORY])

    def _notify(self, settings, run):
        if run["mode"] == "test" or run["status"] == "cancelled":
            return
        if run.get("cookie_invalid"):
            meta = meta_store.read()
            if run["mode"] == "check" and time.time() - meta.get("last_alert", 0) < ALERT_COOLDOWN:
                return
            meta["last_alert"] = time.time()
            meta_store.write(meta)
            notify(settings, "🔐 Cookie TikTok tidak valid", [
                run["error"],
                "Buka panel → tab Cookie → login ulang.",
            ])
            return
        if run["mode"] == "check":
            if run["status"] == "failed":
                notify(settings, "⚠️ Cek cookie gagal", [run.get("error") or "Kesalahan tidak diketahui"])
            return
        icon = {"success": "✅", "partial": "⚠️", "failed": "❌"}.get(run["status"], "ℹ️")
        lines = [f"{run['sent']}/{run['total']} terkirim"]
        if run.get("error"):
            lines.append(run["error"])
        failed = [r["contact"] for r in run["results"] if not r["ok"]]
        if failed:
            lines.append("Gagal: " + ", ".join(failed))
        notify(settings, f"{icon} Streak {run['status']}", lines)

    # --------------------------------------------------------------- scheduler
    def next_run_at(self):
        s = get_settings()
        if not s["schedule_enabled"]:
            return None
        try:
            hh, mm = map(int, s["schedule_time"].split(":"))
            now = datetime.now(_tz(s))
            nxt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if nxt <= now:
                nxt += timedelta(days=1)
            return nxt.strftime("%Y-%m-%d %H:%M") + " " + str(nxt.tzinfo)
        except Exception:  # noqa: BLE001
            return None

    def scheduler_loop(self):
        while True:
            try:
                s = get_settings()
                if s["schedule_enabled"]:
                    now = datetime.now(_tz(s))
                    key = (now.date().isoformat(), s["schedule_time"])
                    if now.strftime("%H:%M") == s["schedule_time"] and key != self._last_fire_key:
                        self._last_fire_key = key
                        try:
                            self.start("send", trigger="schedule")
                        except Busy:
                            pass
                self._keepalive(s)
            except Exception:  # noqa: BLE001
                pass
            time.sleep(20)

    def _keepalive(self, s):
        """Cek berkala agar sesi tetap aktif dan cookie terbaru tersimpan."""
        if not s["keepalive_enabled"] or not cookies_store.read():
            return
        if login_session.active:
            return
        meta = meta_store.read()
        if time.time() - meta.get("last_check", 0) < s["keepalive_hours"] * 3600:
            return
        try:
            self.start("check", trigger="keepalive")
        except Busy:
            return
        meta = meta_store.read()
        meta["last_check"] = time.time()
        meta_store.write(meta)


runner = Runner()
