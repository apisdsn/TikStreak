"""Antrean job browser (send/check/test), worker pool, scheduler harian, dan notifikasi hasil."""
import heapq
import logging
import os
import random
import threading
import time
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import config, db, jobs
from .bot import Cancelled, CookieInvalid, StreakBot
from .config import DATA_DIR
from .notify import notify
from .store import (
    get_account,
    get_run,
    get_settings,
    insert_run,
    kv_get,
    kv_set,
    last_success_at,
    list_accounts,
    new_run_id,
    rename_contact,
    stores,
)

log = logging.getLogger("bara")
MAX_LOG_LINES = 500
PROOFS_DIR = os.path.join(DATA_DIR, "proofs")
CATCHUP_SECONDS = 3 * 3600
ALERT_COOLDOWN = 6 * 3600  # jeda minimal antar alert cookie dari cek otomatis
BREAKAGE_COOLDOWN = 6 * 3600  # jeda alert tampilan TikTok berubah
KEEPALIVE_GUARD = 600      # keepalive tidak mulai bila jadwal kirim jatuh tempo dalam 10 menit


class Busy(Exception):
    pass


def _tz(settings):
    try:
        return ZoneInfo(settings.get("timezone") or config.DEFAULT_TZ)
    except Exception:  # noqa: BLE001
        return ZoneInfo("UTC")


class Runner:
    def __init__(self):
        self.executor = None          # default: _execute_core; tes dapat menggantinya dengan fungsi palsu
        self._runs = {}               # id run -> (run, cancel_event, job) untuk job yang sedang berjalan
        self._lock = threading.RLock()
        self._claim_lock = threading.Lock()
        self._stop = threading.Event()
        self._threads = []
        self._holders = {}
        self._not_before = {}
        self.workers = config.BROWSER_WORKERS
        self.jitter = (config.QUEUE_JITTER_MIN, config.QUEUE_JITTER_MAX)
        self.started = False

    # ------------------------------------------------------------ siklus hidup
        self.scheduler_on = False
        self.last_tick = time.time()
    def start_workers(self, workers=None, scheduler=True):
        if self.started:
            return
        self.started = True
        self._stop.clear()
        if workers:
            self.workers = workers
        back, gone = jobs.recover(CATCHUP_SECONDS)
        for j in gone:
            if j["trigger"] == "schedule":
                self._record_missed(j, "Server Dimulai Ulang dan Jendela Jadwal Sudah Lewat")
        for i in range(self.workers):
            t = threading.Thread(target=self._worker, args=(i,), daemon=True, name=f"bara-worker-{i}")
            t.start()
            self._threads.append(t)
        if scheduler:
            t = threading.Thread(target=self.scheduler_loop, daemon=True, name="bara-scheduler")
            t.start()
            self.scheduler_on = True
            self.last_tick = time.time()
            self._threads.append(t)

    def shutdown(self):
        self._stop.set()
        for t in self._threads:
            t.join(timeout=5)
        self._threads = []
        for h in self._holders.values():
            h.shutdown()
        self._holders = {}
        self.started = False

    # --------------------------------------------------------------- antrean
    def submit(self, account, kind, owner_id, by, message=None):
        """Masukkan job manual ke antrean. Raise jobs.Duplicate bila akun ini sudah punya job sejenis."""
        return jobs.enqueue(account["id"], owner_id, kind, "manual", message=message, by=by)

    def cancel_job(self, job_id, owner_id):
        return jobs.cancel_queued(job_id, owner_id)

    def stop(self, owner_id, account_id=None):
        """Hentikan job milik pengguna yang sedang berjalan. Return jumlah job yang dihentikan."""
        n = 0
        with self._lock:
            for run, cancel, job in self._runs.values():
                if job["owner_id"] == owner_id and (account_id is None or job["account_id"] == account_id):
                    cancel.set()
                    n += 1
        return n

    def running_runs(self, account_ids=None):
        with self._lock:
            runs = [r for r, _, j in self._runs.values() if account_ids is None or j["account_id"] in account_ids]
        return sorted(runs, key=lambda r: r["started_at"], reverse=True)

    def account_busy(self, account_id):
        with self._lock:
            return any(j["account_id"] == account_id for _, _, j in self._runs.values())

    @property
    def current(self):
        """Run berjalan terbaru (kompatibilitas)."""
        r = self.running_runs()
        return r[0] if r else None

    # ----------------------------------------------------------- pemilihan job
    def _login_accounts(self):
        from .login import login_mgr
        return login_mgr.active_account_ids()

    def _due_soon(self, s):
        """Ada jadwal kirim yang jatuh tempo dalam 10 menit, atau job jadwal yang masih antre."""
        if any(j["trigger"] == "schedule" for j in jobs.queued()):
            return True
        for acc in list_accounts():
            for sched in acc["schedules"]:
                if sched["enabled"]:
                    try:
                        now, due = self._slot(sched, s)
                    except Exception:  # noqa: BLE001
                        continue
                    if -KEEPALIVE_GUARD <= (now - due).total_seconds() <= KEEPALIVE_GUARD:
                        return True
        return False

    def next_job(self):
        """Job antre berikutnya yang boleh jalan sekarang, sudah ditandai berjalan; None bila tidak ada."""
        with self._claim_lock:
            self._expire_overdue()
            running_acc = {j["account_id"] for j in jobs.running()}
            login_acc = self._login_accounts()
            now = time.time()
            s = get_settings()
            soon = None
            for j in jobs.queued():
                if j["due_at"] > now or j["account_id"] in running_acc or j["account_id"] in login_acc:
                    continue
                if j["trigger"] == "keepalive":
                    if soon is None:
                        soon = self._due_soon(s)
                    if soon:
                        continue
                if jobs.claim(j["id"]):
                    return jobs.get(j["id"])
            return None

    def _expire_overdue(self):
        for j in jobs.overdue(CATCHUP_SECONDS):
            jobs.finish(j["id"], "expired", reason="Antrean Terlalu Padat, Jendela Jadwal Sudah Lewat")
            self._record_missed(j, "Antrean Terlalu Padat, Jendela Jadwal Sudah Lewat")

    def _record_missed(self, job, reason):
        acc = get_account(job["account_id"])
        if not acc:
            return
        now = datetime.now().isoformat(timespec="seconds")
        run = {"id": new_run_id(), "account": {"id": acc["id"], "name": acc["name"]}, "owner_id": acc.get("owner_id"),
               "mode": job["kind"], "trigger": job["trigger"], "by": "system", "label": job.get("label"), "status": "expired",
               "started_at": now, "finished_at": now, "sent": 0, "total": 0, "message": job.get("message"), "error": reason,
               "results": [], "logs": [{"t": datetime.now().strftime("%H:%M:%S"), "level": "warning", "msg": reason}]}
        insert_run(run)
        try:
            self._notify(get_settings(), run)
        except Exception:  # noqa: BLE001
            log.exception("notifikasi job terlewat gagal")

    # ------------------------------------------------------------------ worker
    def _worker(self, idx):
        while not self._stop.is_set():
            try:
                if time.time() < self._not_before.get(idx, 0):
                    self._stop.wait(0.5)
                    continue
                job = self.next_job()
                if not job:
                    self._stop.wait(1.0)
                    continue
                try:
                    self._run_job(job, idx)
                finally:
                    lo, hi = self.jitter  # jeda acak antar job agar kiriman tidak datang beruntun dari satu IP
                    self._not_before[idx] = time.time() + random.uniform(lo, hi)
            except Exception:  # noqa: BLE001
                log.exception("worker %s galat", idx)
                self._stop.wait(2)

    def _provider(self, idx):
        from .pool import BrowserHolder
        h = self._holders.get(idx)
        if h is None:
            h = self._holders[idx] = BrowserHolder(idx)
        return h

    def _log_fn(self, run):
        def log_line(msg, level="info"):
            line = {"t": datetime.now().strftime("%H:%M:%S"), "level": level, "msg": msg}
            run["logs"].append(line)
            if len(run["logs"]) > MAX_LOG_LINES:
                del run["logs"][: len(run["logs"]) - MAX_LOG_LINES]
        return log_line

    def _run_job(self, job, idx=0):
        acc = get_account(job["account_id"])
        if not acc:
            jobs.finish(job["id"], "cancelled", reason="Akun Dihapus")
            return
        run = {
            "id": new_run_id(), "account": {"id": acc["id"], "name": acc["name"]}, "owner_id": acc.get("owner_id"),
            "mode": job["kind"], "trigger": job["trigger"], "by": job.get("by") if job["trigger"] == "manual" else "system",
            "label": job.get("label"), "status": "running", "started_at": datetime.now().isoformat(timespec="seconds"),
            "finished_at": None, "sent": 0, "total": 0, "message": job.get("message"), "only": job.get("contacts"),
            "results": [], "logs": [],
        }
        cancel = threading.Event()
        with self._lock:
            self._runs[run["id"]] = (run, cancel, job)
        jobs.set_run(job["id"], run["id"])
        bot = None
        try:
            fn = self.executor or self._execute_core
            bot = fn(run, job, cancel, lambda: self._provider(idx))
        except Exception as e:  # noqa: BLE001
            run["status"] = "failed"
            run["error"] = str(e)
            self._log_fn(run)(f"Gagal: {e}", "error")
        try:
            self._update_meta(run, bot)
            run["finished_at"] = datetime.now().isoformat(timespec="seconds")
            self._save_history(run)
            self._notify(get_settings(), run)
        finally:
            with self._lock:
                self._runs.pop(run["id"], None)
            jobs.finish(job["id"], {"cancelled": "cancelled", "failed": "failed"}.get(run["status"], "done"), run["id"], run.get("error"))

    def _execute_core(self, run, job, cancel, get_provider):
        """Jalankan bot untuk satu job. Return objek bot (untuk pembaruan meta)."""
        settings = get_settings()
        log_line = self._log_fn(run)
        mode = run["mode"]
        log_line({"test": "Mode Uji (Tidak Mengirim Pesan)", "check": "Cek & Perbarui Cookie"}.get(mode, "Mulai Mengirim Streak"))
        bot = None
        st = stores(run["account"]["id"])
        try:
            contacts = st.contacts.read()
            if run.get("only") is not None:  # jadwal dengan kontak tertentu
                wanted = {c.lower() for c in run["only"]}
                contacts = [c for c in contacts if c.lower() in wanted]
                if not contacts:
                    raise RuntimeError("Tidak Ada Kontak Terpilih untuk Jadwal Ini (Mungkin Sudah Dihapus)")
            bot = StreakBot(settings, log_line, cancel, st.cookies, test_mode=(mode == "test"),
                            message=run.get("message"), check_only=(mode == "check"),
                            proof_dir=os.path.join(PROOFS_DIR, run["id"]), convs_store=st.convs,
                            account_id=run["account"]["id"], provider=get_provider())
            res = bot.run(contacts)
            run.update(res)
            for r in res["results"]:  # kontak yang berganti nama dikenali lewat ID percakapan
                new = (r.get("evidence") or {}).get("renamed_to")
                if new:
                    rename_contact(run["account"]["id"], r["contact"], new)
                    log_line(f"Kontak Diperbarui Otomatis: {r['contact']} → {new}")
            log_line("Cookie Valid" if mode == "check" else f"Selesai: {res['sent']}/{res['total']}")
        except Cancelled:
            run["status"] = "cancelled"
            log_line("Dihentikan Oleh Pengguna", "warning")
        except CookieInvalid as e:
            run["status"] = "failed"
            self._after_run(get_settings(), run)
            run["error"] = str(e)
            run["cookie_invalid"] = True
            log_line(f"Gagal: {e}", "error")
        except Exception as e:  # noqa: BLE001
            run["status"] = "failed"
            run["error"] = str(e)
            log_line(f"Gagal: {e}", "error")
        return bot

    def _update_meta(self, run, bot):
        meta_store = stores(run["account"]["id"]).meta
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
        insert_run(run)  # retensi per akun (HISTORY_DAYS / HISTORY_PER_ACCOUNT) diterapkan di sini

    def _targets(self, settings, run):
        """Kanal penerima: pribadi pemilik akun, plus global bila pemiliknya admin. Tidak ada kanal yang dipakai dua kali."""
        from .auth import get_user, user_notify
        acc = get_account(run["account"]["id"])
        owner = get_user(acc.get("owner_id")) if acc and acc.get("owner_id") else None
        owner_active = bool(owner) and not owner.get("disabled")
        out, used = [], set()

        def add(cfg):
            c = dict(cfg)
            if c.get("discord_enabled"):
                key = ("d", c.get("discord_webhook"))
                if not c.get("discord_webhook") or key in used:
                    c["discord_enabled"] = False
                else:
                    used.add(key)
            if c.get("telegram_enabled"):
                key = ("t", c.get("telegram_token"), c.get("telegram_chat_id"))
                if not c.get("telegram_token") or not c.get("telegram_chat_id") or key in used:
                    c["telegram_enabled"] = False
                else:
                    used.add(key)
            if c.get("discord_enabled") or c.get("telegram_enabled"):
                out.append(c)

        if owner_active:
            add(user_notify(owner))
        if owner_active and owner["role"] == "admin":  # saluran global hanya untuk akun milik admin
            add(settings)
        return out

    def _notify(self, settings, run):
        if run["mode"] == "test" or run["status"] == "cancelled":
            return
        targets = self._targets(settings, run)
        if not targets:
            return
        who = f"[{run['account']['name']}] " if len(list_accounts()) > 1 else ""
        if run["status"] == "expired":
            for t in targets:
                notify(t, f"⏰ {who}Jadwal {run.get('label') or ''} Terlewat".replace("  ", " "), [run.get("error") or "Antrean Terlalu Padat"])
            return
        if run.get("cookie_invalid"):
            meta_store = stores(run["account"]["id"]).meta
            meta = meta_store.read()
            if run["mode"] == "check" and time.time() - meta.get("last_alert", 0) < ALERT_COOLDOWN:
                return
            meta["last_alert"] = time.time()
            meta_store.write(meta)
            for t in targets:
                notify(t, f"🔐 {who}Cookie TikTok tidak valid", [
                    run["error"],
                    "Buka panel → tab Cookie → login ulang.",
                ])
            return
        if run["mode"] == "check":
            if run["status"] == "failed":
                for t in targets:
                    notify(t, f"⚠️ {who}Cek cookie gagal", [run.get("error") or "Kesalahan tidak diketahui"])
            return
        icon = {"success": "✅", "partial": "⚠️", "failed": "❌"}.get(run["status"], "ℹ️")
        lines = [f"{run['sent']}/{run['total']} terkirim · {self._span(run)}"]
        if run.get("label"):
            lines.insert(0, f"Jadwal {run['label']}")
        if run["mode"] == "send":
            lines.append(f"Pesan: \"{run.get('message') or settings['message']}\"")
        if run.get("error"):
            lines.append(run["error"])
        proofs = []
        for r in run["results"]:
            if r["ok"]:
                lines.append(f"✅ {r['contact']} — {r.get('sent_at') or 'ok'}{self._evidence(r.get('evidence'))}")
            else:
                lines.append(f"❌ {r['contact']} — {r.get('error') or 'gagal'}")
            if r.get("proof"):
                path = os.path.join(PROOFS_DIR, run["id"], r["proof"])
                try:
                    with open(path, "rb") as f:
                        proofs.append((f"{r['contact']} {r.get('sent_at') or ''}".strip(), f.read()))
                except OSError:
                    pass
        for t in targets:  # lampiran mengikuti pengaturan saluran penerima
            files = proofs if t.get("notify_screenshot") else []
            tl = lines + (["Bukti: screenshot chat terlampir"] if files else [])
            notify(t, f"{icon} {who}Streak {run['status']}", tl, files)

    @staticmethod
    def _evidence(ev):
        if not ev:
            return ""
        parts = []
        if ev.get("renamed_to"):
            parts.append(f"nama baru {ev['renamed_to']}, diperbarui otomatis")
        if ev.get("chat"):
            parts.append(f"chat {ev['chat']} ✓")
        if ev.get("bubble"):
            parts.append("bubble terverifikasi")
        if ev.get("list_time"):
            parts.append(f"daftar chat {ev['list_time']}")
        return " · " + " · ".join(parts) if parts else ""

    @staticmethod
    def _span(run):
        try:
            a = datetime.fromisoformat(run["started_at"])
            b = datetime.fromisoformat(run["finished_at"])
            sec = int((b - a).total_seconds())
            return f"{a.strftime('%H:%M:%S')} ({sec // 60}m {sec % 60}s)"
        except Exception:  # noqa: BLE001
            return run.get("started_at", "")

    # --------------------------------------------------------------- estimasi
    def avg_duration(self, account_id, kind, n_contacts=0):
        """Rata-rata durasi 5 run terakhir akun untuk jenis ini; bila belum ada: 30 dtk per kontak + 20 dtk."""
        from . import db
        rows = db.q("SELECT started_at, finished_at FROM runs WHERE account_id=? AND mode=? AND status IN ('success','partial','failed') "
                    "AND finished_at IS NOT NULL ORDER BY started_at DESC LIMIT 5", (account_id, kind))
        ds = []
        for r in rows:
            try:
                ds.append((datetime.fromisoformat(r["finished_at"]) - datetime.fromisoformat(r["started_at"])).total_seconds())
            except Exception:  # noqa: BLE001
                pass
        if ds:
            return max(5.0, sum(ds) / len(ds))
        return 30.0 if kind == "check" else n_contacts * 30.0 + 20.0

    def _n_contacts(self, job):
        if job.get("contacts") is not None:
            return len(job["contacts"])
        return len(stores(job["account_id"]).contacts.read())

    def snapshot(self):
        """Simulasi antrean: posisi dan perkiraan mulai/selesai setiap job (waktu epoch)."""
        now = time.time()
        free = []
        out = {}
        run_jobs = jobs.running()
        for j in run_jobs:
            est = self.avg_duration(j["account_id"], j["kind"], self._n_contacts(j))
            end = max(now + 10, (j["started_at"] or now) + est)
            heapq.heappush(free, end)
            out[j["id"]] = {"id": j["id"], "state": "running", "position": 0, "eta": j["started_at"], "est": est, "end": end}
        while len(free) < self.workers:
            heapq.heappush(free, now)
        while len(free) > self.workers and len(run_jobs) > self.workers:
            heapq.heappop(free)
        avg_jitter = sum(self.jitter) / 2
        for pos, j in enumerate(jobs.queued(), start=1):
            est = self.avg_duration(j["account_id"], j["kind"], self._n_contacts(j))
            start = max(heapq.heappop(free) if free else now, now, j["due_at"])
            heapq.heappush(free, start + est + avg_jitter)
            out[j["id"]] = {"id": j["id"], "state": "queued", "position": pos, "eta": start, "est": est, "end": start + est}
        return out

    def view_for(self, owner_id):
        """Info antrean untuk satu pengguna: job miliknya (posisi, ETA) + hitungan agregat tanpa nama."""
        snap = self.snapshot()
        mine = []
        for j in jobs.of_owner(owner_id):
            s = snap.get(j["id"], {})
            acc = get_account(j["account_id"])
            mine.append({"id": j["id"], "account_id": j["account_id"], "account_name": acc["name"] if acc else None, "kind": j["kind"],
                         "trigger": j["trigger"], "label": j.get("label"), "state": s.get("state", j["status"]),
                         "position": s.get("position", 0), "eta": datetime.fromtimestamp(s["eta"]).strftime("%H:%M") if s.get("eta") else None,
                         "eta_epoch": s.get("eta")})
        c = jobs.counts()
        return {"mine": mine, "queued": c["queued"], "running": c["running"], "workers": self.workers}

    def check_midnight(self):
        """Peringatkan pemilik (sekali sehari) bila jadwal kirimnya diperkirakan baru terkirim setelah tengah malam."""
        s = get_settings()
        tz = _tz(s)
        snap = self.snapshot()
        warned = set()
        for j in jobs.queued():
            if j["trigger"] != "schedule" or j["owner_id"] in warned:
                continue
            info = snap.get(j["id"])
            if not info:
                continue
            due = datetime.fromtimestamp(j["due_at"], tz)
            midnight = (due.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).timestamp()
            if info["end"] > midnight:
                warned.add(j["owner_id"])
                key = "qwarn:" + str(j["owner_id"])
                today = datetime.now(tz).strftime("%Y-%m-%d")
                if kv_get(key) == today:
                    continue
                kv_set(key, today)
                acc = get_account(j["account_id"])
                fake = {"account": {"id": j["account_id"], "name": acc["name"] if acc else ""}, "mode": "send", "status": "warning"}
                for t in self._targets(s, fake):
                    notify(t, "⚠️ Antrean Padat, Pesan Mungkin Terkirim setelah Tengah Malam",
                           [f"Jadwal {j.get('label') or ''} diperkirakan selesai pukul {datetime.fromtimestamp(info['end'], tz).strftime('%H:%M')}"])

    def load_slots(self):
        """Jumlah jadwal aktif seluruh panel per slot 30 menit (hanya hitungan)."""
        slots = {}
        for acc in list_accounts():
            for sched in acc["schedules"]:
                if sched["enabled"]:
                    h, m = map(int, sched["time"].split(":"))
                    key = f"{h:02d}:{(m // 30) * 30:02d}"
                    slots[key] = slots.get(key, 0) + 1
        return slots

    # --------------------------------------------------------------- scheduler
    @staticmethod
    def _slot(sched, s):
        """Waktu sekarang dan waktu jadwal hari ini (aware) menurut timezone pengaturan."""
        hh, mm = map(int, sched["time"].split(":"))
        now = datetime.now(_tz(s))
        return now, now.replace(hour=hh, minute=mm, second=0, microsecond=0)

    def next_run_at(self, account_id=None):
        s = get_settings()
        best = None
        for acc in list_accounts():
            if account_id and acc["id"] != account_id:
                continue
            for sched in acc["schedules"]:
                if not sched["enabled"]:
                    continue
                try:
                    now, nxt = self._slot(sched, s)
                    if nxt <= now:
                        nxt += timedelta(days=1)
                except Exception:  # noqa: BLE001
                    continue
                if best is None or nxt < best:
                    best = nxt
        return best.strftime("%Y-%m-%d %H:%M") + " " + str(best.tzinfo) if best else None

    def next_schedule(self, account_id):
        """Jadwal aktif terdekat untuk satu akun: {time, at, epoch, contacts, message} atau None."""
        s = get_settings()
        acc = get_account(account_id)
        best, pick = None, None
        for sched in (acc["schedules"] if acc else []):
            if not sched["enabled"]:
                continue
            try:
                now, nxt = self._slot(sched, s)
                if nxt <= now:
                    nxt += timedelta(days=1)
            except Exception:  # noqa: BLE001
                continue
            if best is None or nxt < best:
                best, pick = nxt, sched
        if not best:
            return None
        return {
            "time": pick["time"],
            "at": best.strftime("%Y-%m-%d %H:%M") + " " + str(best.tzinfo),
            "epoch": int(best.timestamp()),
            "contacts": pick.get("contacts"),
            "message": pick.get("message") or "",
        }

    def scheduler_loop(self):
        n = 0
        while not self._stop.is_set():
            try:
                s = get_settings()
                accounts = list_accounts()
                for acc in accounts:
                    for sched in acc["schedules"]:
                        if sched["enabled"]:
                            self._fire_if_due(acc, sched, s)
                for acc in accounts:
                    self._keepalive(acc, accounts, s)
                if n % 3 == 0:
                    self.check_midnight()
                if n % 180 == 0:
                    jobs.prune()
            except Exception:  # noqa: BLE001
                log.exception("scheduler galat")
            n += 1
            self._stop.wait(20)

    def _fire_if_due(self, acc, sched, s):
        """Masukkan jadwal yang jatuh tempo ke antrean satu kali, lalu tandai sudah ditembakkan."""
        now, due = self._slot(sched, s)
        key = due.strftime("%Y-%m-%d %H:%M")
        late = (now - due).total_seconds()
        meta_store = stores(acc["id"]).meta
        meta = meta_store.read()
        fired = meta.get("fired", {})
        blocked = meta.get("blocked", {})
        if sched["id"] == "s1" and "s1" not in fired and meta.get("last_schedule"):
            fired["s1"] = meta["last_schedule"]  # catatan dari format lama
        if fired.get(sched["id"]) == key:
            return
        # Masuk antrean tepat waktu; bila terlewat (restart/antrean penuh) kejar hingga 3 jam
        if 0 <= late < CATCHUP_SECONDS:
            try:
                jobs.enqueue(acc["id"], acc.get("owner_id"), "send", "schedule", label=sched["time"], message=sched.get("message") or None,
                             contacts=sched.get("contacts"), due_at=due.timestamp())
            except jobs.Duplicate:
                blocked[sched["id"]] = key  # sudah ada job kirim akun ini; dicoba lagi 20 detik kemudian
                meta["blocked"] = blocked
                meta_store.write(meta)
                return
            fired[sched["id"]] = key
            meta["fired"] = fired
            blocked.pop(sched["id"], None)
            meta["blocked"] = blocked
            meta_store.write(meta)
        elif late >= CATCHUP_SECONDS and blocked.get(sched["id"]) == key:
            # pernah mencoba masuk antrean tetapi terhalang sampai jendela habis: catat sebagai terlewat
            fired[sched["id"]] = key
            blocked.pop(sched["id"], None)
            meta["fired"], meta["blocked"] = fired, blocked
            meta_store.write(meta)
            self._record_missed({"account_id": acc["id"], "kind": "send", "trigger": "schedule", "label": sched["time"],
                                 "message": sched.get("message")}, "Antrean Terlalu Padat, Jendela Jadwal Sudah Lewat")

    def _keepalive(self, acc, accounts, s):
        """Cek cookie berkala agar sesi tetap aktif: masukkan job 'check' berprioritas rendah ke antrean."""
        st = stores(acc["id"])
        if not s["keepalive_enabled"] or not st.cookies.read():
            return False
            self.last_tick = time.time()
        meta = st.meta.read()
        if time.time() - meta.get("last_check", 0) < s["keepalive_hours"] * 3600:
            return False
    # ------------------------------------------------------- alert kegagalan Bara sendiri
    CONTACT_ERRORS = ("Kontak Tidak Ditemukan", "Chat yang Terbuka Milik")  # masalah satu kontak, bukan tanda tampilan TikTok berubah

    def _after_run(self, settings, run):
        try:
            self._breakage_alert(settings, run)
        except Exception:  # noqa: BLE001
            log.exception("alert kegagalan galat")

    def _breakage_alert(self, settings, run):
        """Semua kontak gagal pada cookie yang valid: kemungkinan tampilan TikTok berubah. Jeda 6 jam per akun dan untuk kanal sistem."""
        res = run.get("results") or []
        if run["mode"] != "send" or run.get("cookie_invalid") or not res or any(r.get("ok") for r in res):
            return
        if all(any(m in (r.get("error") or "") for m in self.CONTACT_ERRORS) for r in res):
            return
        now = time.time()
        aid = run["account"]["id"]
        own = self._targets(settings, run)
        if now - float(kv_get("brk:" + aid, 0) or 0) >= BREAKAGE_COOLDOWN:
            kv_set("brk:" + aid, now)
            for t in own:
                notify(t, "🛠️ Semua Kontak Gagal, Kemungkinan Tampilan TikTok Berubah",
                       [f"Akun {run['account']['name']}: {len(res)} kontak gagal, cookie masih valid.", "Cek screenshot di riwayat, lalu perbarui Bara bila perlu."])
        if now - float(kv_get("brk-sys", 0) or 0) >= BREAKAGE_COOLDOWN:
            used_d = {t.get("discord_webhook") for t in own if t.get("discord_enabled")}
            used_t = {(t.get("telegram_token"), t.get("telegram_chat_id")) for t in own if t.get("telegram_enabled")}
            sys_t = [t for t in self._global_channels(settings)
                     if not (t.get("discord_enabled") and t["discord_webhook"] in used_d)
                     and not (t.get("telegram_enabled") and (t["telegram_token"], t["telegram_chat_id"]) in used_t)]
            if sys_t:
                kv_set("brk-sys", now)
                for t in sys_t:  # peringatan sistem: tanpa nama akun atau kontak
                    notify(t, "🛠️ Peringatan Sistem: Pengiriman Gagal untuk Semua Kontak pada Satu Akun",
                           ["Kemungkinan tampilan TikTok berubah. Periksa Bara dan perbarui bila perlu."])

    @staticmethod
    def _global_channels(settings):
        c = dict(settings)
        out = []
        if c.get("discord_enabled") and c.get("discord_webhook"):
            out.append({**c, "telegram_enabled": False})
        if c.get("telegram_enabled") and c.get("telegram_token") and c.get("telegram_chat_id"):
            out.append({**c, "discord_enabled": False})
        return out

    def check_stalled(self):
        """Akun dengan jadwal aktif dan cookie tetapi tanpa kiriman sukses selama 24 jam: peringatkan pemilik, sekali sehari."""
        s = get_settings()
        today = datetime.now(_tz(s)).strftime("%Y-%m-%d")
        for acc in list_accounts():
            if not any(x["enabled"] for x in acc["schedules"]):
                continue
            st = stores(acc["id"])
            if not st.cookies.read() or st.meta.read().get("invalid"):
                continue  # masalah cookie punya alert sendiri
            row = db.q1("SELECT created_at FROM accounts WHERE id=?", (acc["id"],))
            ref = None
            for v in (row and row["created_at"], last_success_at(acc["id"])):
                try:
                    d = datetime.fromisoformat(v) if v else None
                except ValueError:
                    d = None
                if d and (ref is None or d > ref):
                    ref = d
            if ref is None or datetime.now() - ref < timedelta(hours=24):
                continue
            key = "nosucc:" + acc["id"]
            if kv_get(key) == today:
                continue
            kv_set(key, today)
            fake = {"account": {"id": acc["id"], "name": acc["name"]}, "mode": "send", "status": "warning"}
            for t in self._targets(s, fake):
                notify(t, "⚠️ Belum Ada Pesan Terkirim dalam 24 Jam",
                       [f"Akun {acc['name']} punya jadwal aktif dan cookie, tetapi tidak ada kiriman sukses.", "Cek riwayat dan log di panel."])

    # --------------------------------------------------------------- kesehatan
    def deep_health(self):
        now = time.time()
        workers = [t for t in self._threads if t.name.startswith("bara-worker")]
        alive = sum(1 for t in workers if t.is_alive())
        info = {"scheduler_age": round(now - self.last_tick, 1) if self.scheduler_on else None,
                "workers": {"total": len(workers), "alive": alive}, "db": True}
        ok = True
        if self.scheduler_on and now - self.last_tick > 120:
            ok = False
        if alive < len(workers):
            ok = False
        try:
            db.q1("SELECT 1")
        except Exception:  # noqa: BLE001
            info["db"] = False
            ok = False
        info["status"] = "ok" if ok else "fail"
        return ok, info

    def ping(self):
        """Dead-man's switch: panggil HEALTHCHECK_PING_URL selama kesehatan mendalam OK."""
        url = config.HEALTHCHECK_PING_URL
        if not url or not self.deep_health()[0]:
            return False
        try:
            import urllib.request
            urllib.request.urlopen(url, timeout=10).read(1)
            return True
        except Exception as e:  # noqa: BLE001
            log.warning("ping healthcheck gagal: %s", e)
            return False

        try:
            jobs.enqueue(acc["id"], acc.get("owner_id"), "check", "keepalive")
        except jobs.Duplicate:
            return False
        meta = st.meta.read()
        meta["last_check"] = time.time()
        st.meta.write(meta)
        return True


runner = Runner()
