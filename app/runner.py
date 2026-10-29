"""Menjalankan bot di thread, menyimpan log live + riwayat, dan scheduler harian."""
import threading
import time
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import config
from .bot import Cancelled, StreakBot
from .notify import notify
from .store import contacts_store, get_settings, history_store

MAX_HISTORY = 50
MAX_LOG_LINES = 500


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
        test = run["mode"] == "test"
        log("Mode uji (tidak mengirim pesan)" if test else "Mulai mengirim streak")
        try:
            contacts = contacts_store.read()
            bot = StreakBot(settings, log, self._cancel, test_mode=test, message=message)
            res = bot.run(contacts)
            run.update(res)
            log(f"Selesai: {res['sent']}/{res['total']}")
        except Cancelled:
            run["status"] = "cancelled"
            log("Dihentikan oleh pengguna", "warning")
        except Exception as e:  # noqa: BLE001
            run["status"] = "failed"
            run["error"] = str(e)
            log(f"Gagal: {e}", "error")
        run["finished_at"] = datetime.now().isoformat(timespec="seconds")
        self._save_history(run)
        self._notify(settings, run)

    def _save_history(self, run):
        hist = history_store.read()
        hist.insert(0, {k: v for k, v in run.items()})
        history_store.write(hist[:MAX_HISTORY])

    def _notify(self, settings, run):
        if run["mode"] == "test" or run["status"] == "cancelled":
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
            except Exception:  # noqa: BLE001
                pass
            time.sleep(20)


runner = Runner()
