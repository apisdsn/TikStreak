"""Migrasi sekali jalan dari data JSON (versi lama) ke SQLite. Aman dipanggil berulang."""
import json
import logging
import os
import shutil
import time

from . import crypto, db
from .config import DATA_DIR

log = logging.getLogger("bara")
FLAG = "kv:json_migrated"
SECRETS = ("telegram_token", "discord_webhook")
LEGACY_SETTINGS = ("schedules", "schedule_enabled", "schedule_time", "notify_all_accounts")
ROOT_FILES = ("users.json", "sessions.json", "settings.json", "accounts.json", "history.json",
              "cookies.json", "contacts.json", "meta.json", "convs.json")


def _p(*a):
    return os.path.join(DATA_DIR, *a)


def _read(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _j(v):
    return json.dumps(v, ensure_ascii=False)


def _has_legacy():
    return any(os.path.exists(_p(f)) for f in ROOT_FILES) or os.path.isdir(_p("accounts"))


def _acct_file(aid, name, default):
    v = _read(_p("accounts", aid, name), None)
    if v is None and aid == "main":  # format satu-akun sebelum multi-akun
        v = _read(_p(name), None)
    return default if v is None else v


def run():
    db.init()
    if db.q1("SELECT 1 FROM settings WHERE key=?", (FLAG,)):
        return
    if not _has_legacy():
        db.x("INSERT OR REPLACE INTO settings(key, value_json) VALUES(?, 'true')", (FLAG,))
        return
    stats = {}
    with db.tx():
        users = _read(_p("users.json"), [])
        for u in users:
            nj = crypto.encrypt(_j(u["notify"])) if u.get("notify") else None
            db.x("INSERT OR IGNORE INTO users(id, username, pw_hash, salt, iterations, role, disabled, created_at, pw_changed_at, notify_json) "
                 "VALUES(?,?,?,?,?,?,?,?,?,?)", (u["id"], u["username"], u["pw_hash"], u["salt"], u["iterations"], u["role"],
                                                 1 if u.get("disabled") else 0, u.get("created_at"), u.get("pw_changed_at"), nj))
        stats["users"] = len(users)
        user_ids = {u["id"] for u in users}
        now = time.time()
        n = 0
        for h, s in (_read(_p("sessions.json"), {}) or {}).items():
            if s.get("user_id") in user_ids and s.get("expires", 0) > now:
                db.x("INSERT OR IGNORE INTO sessions(token_hash, user_id, created_at, expires_at) VALUES(?,?,?,?)",
                     (h, s["user_id"], s.get("created"), s["expires"]))
                n += 1
        stats["sessions"] = n
        raw = _read(_p("settings.json"), {})
        for k, v in raw.items():
            if k in LEGACY_SETTINGS:
                continue
            if k in SECRETS:
                v = crypto.enc_text(v)
            db.x("INSERT OR REPLACE INTO settings(key, value_json) VALUES(?,?)", (k, _j(v)))
        accounts = _read(_p("accounts.json"), None)
        if accounts is None:
            sched = raw.get("schedules")
            if sched is None and "schedule_time" in raw:
                sched = [{"id": "s1", "enabled": bool(raw.get("schedule_enabled", False)), "time": raw["schedule_time"], "message": ""}]
            accounts = [{"id": "main", "name": "Utama", "schedules": sched or []}]
        owner_of = {}
        seen = set()
        for a in accounts:
            owner = a.get("owner_id") if a.get("owner_id") in user_ids else None
            name = a["name"]
            i = 2
            while (owner, name.lower()) in seen:
                name = f"{a['name']} ({i})"
                i += 1
            seen.add((owner, name.lower()))
            owner_of[a["id"]] = owner
            db.x("INSERT OR IGNORE INTO accounts(id, owner_id, name, created_at) VALUES(?,?,?,?)",
                 (a["id"], owner, name, time.strftime("%Y-%m-%dT%H:%M:%S")))
            for pos, s in enumerate(a.get("schedules") or []):
                c = s.get("contacts")
                db.x("INSERT OR IGNORE INTO schedules(id, account_id, time, enabled, message, contacts_json, position) VALUES(?,?,?,?,?,?,?)",
                     (s.get("id") or f"s{pos + 1}", a["id"], s["time"], 1 if s.get("enabled", True) else 0, s.get("message") or "",
                      None if c is None else _j(c), pos))
            for pos, cname in enumerate(_acct_file(a["id"], "contacts.json", [])):
                db.x("INSERT OR IGNORE INTO contacts(account_id, name, position) VALUES(?,?,?)", (a["id"], cname, pos))
            for k, v in (_acct_file(a["id"], "convs.json", {}) or {}).items():
                db.x("INSERT OR IGNORE INTO convs(account_id, name_lc, conv_id) VALUES(?,?,?)", (a["id"], k, v))
            cookies = _acct_file(a["id"], "cookies.json", [])
            meta = _acct_file(a["id"], "meta.json", {})
            db.x("INSERT OR REPLACE INTO account_state(account_id, cookies_enc, cookies_updated_at, last_check, cookie_status, meta_json) VALUES(?,?,?,?,?,?)",
                 (a["id"], crypto.encrypt(_j(cookies)) if cookies else None, time.time() if cookies else None, meta.get("last_check"),
                  "invalid" if meta.get("invalid") else ("ok" if meta.get("last_ok") else None), _j(meta)))
        stats["accounts"] = len(accounts)
        runs = _read(_p("history.json"), [])
        for r in runs:
            acc = r.get("account") or {}
            db.x("INSERT OR IGNORE INTO runs(id, account_id, owner_id, account_name, mode, trigger, run_by, label, status, started_at, "
                 "finished_at, sent, total, error, message, results_json, logs_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                 (r["id"], acc.get("id"), owner_of.get(acc.get("id")), acc.get("name"), r.get("mode"), r.get("trigger"), r.get("by"),
                  r.get("label"), r.get("status"), r.get("started_at"), r.get("finished_at"), r.get("sent", 0), r.get("total", 0),
                  r.get("error"), r.get("message"), _j(r.get("results", [])), _j(r.get("logs", []))))
        stats["runs"] = len(runs)
        db.x("INSERT OR REPLACE INTO settings(key, value_json) VALUES(?, 'true')", (FLAG,))
    # cadangkan file JSON lama (tidak dihapus); bukti (proofs/) tetap di tempatnya
    backup = _p("backup-json-" + time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(backup, exist_ok=True)
    for f in ROOT_FILES:
        if os.path.exists(_p(f)):
            shutil.move(_p(f), os.path.join(backup, f))
    if os.path.isdir(_p("accounts")):
        shutil.move(_p("accounts"), os.path.join(backup, "accounts"))
    log.warning("Data JSON dimigrasikan ke SQLite %s; salinan lama di %s", stats, backup)
