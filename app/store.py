"""Akses data panel (SQLite). Antarmuka lama (read/write per akun) dipertahankan lewat adapter."""
import json
import os
import shutil
import uuid
from datetime import datetime, timedelta

from . import config, crypto, db
from .config import DATA_DIR

DEFAULT_SETTINGS = {
    "message": "🔥 Streak 🔥",
    "timezone": "",
    "telegram_enabled": False,
    "telegram_token": "",
    "telegram_chat_id": "",
    "discord_enabled": False,
    "discord_webhook": "",
    "notify_screenshot": False,
    "keepalive_enabled": True,
    "keepalive_hours": 12,
    "page_load_wait": 5,
    "element_wait": 3,
    "send_delay": 2,
}
SECRET_SETTINGS = ("telegram_token", "discord_webhook")
LEGACY_SETTINGS = ("schedules", "schedule_enabled", "schedule_time", "notify_all_accounts")


def _j(v):
    return json.dumps(v, ensure_ascii=False)


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


# --------------------------------------------------------------- pengaturan
def get_settings():
    out = dict(DEFAULT_SETTINGS)
    for r in db.q("SELECT key, value_json FROM settings"):
        k = r["key"]
        if k not in DEFAULT_SETTINGS:
            continue
        try:
            v = json.loads(r["value_json"])
        except (TypeError, ValueError):
            continue
        out[k] = crypto.dec_text(v) if k in SECRET_SETTINGS else v
    return out


def save_settings(data):
    with db.tx():
        for k in DEFAULT_SETTINGS:
            if k not in data:
                continue
            v = data[k]
            if k in SECRET_SETTINGS:
                v = crypto.enc_text(v)
            db.x("INSERT INTO settings(key, value_json) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json",
                 (k, _j(v)))


def kv_get(key, default=None):
    r = db.q1("SELECT value_json FROM settings WHERE key=?", ("kv:" + key,))
    return json.loads(r["value_json"]) if r else default


def kv_set(key, value):
    db.x("INSERT INTO settings(key, value_json) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json",
         ("kv:" + key, _j(value)))


# -------------------------------------------------------------------- akun
def _schedules_of(aid):
    out = []
    for r in db.q("SELECT * FROM schedules WHERE account_id=? ORDER BY position", (aid,)):
        out.append({"id": r["id"], "enabled": bool(r["enabled"]), "time": r["time"], "message": r["message"] or "",
                    "contacts": json.loads(r["contacts_json"]) if r["contacts_json"] is not None else None})
    return out


def _account(row, scheds):
    return {"id": row["id"], "name": row["name"], "owner_id": row["owner_id"], "schedules": scheds.get(row["id"], []),
            "created_at": row["created_at"]}


def list_accounts():
    scheds = {}
    for r in db.q("SELECT * FROM schedules ORDER BY account_id, position"):
        scheds.setdefault(r["account_id"], []).append({
            "id": r["id"], "enabled": bool(r["enabled"]), "time": r["time"], "message": r["message"] or "",
            "contacts": json.loads(r["contacts_json"]) if r["contacts_json"] is not None else None})
    return [_account(r, scheds) for r in db.q("SELECT * FROM accounts ORDER BY created_at, rowid")]


def accounts_of(owner_id):
    return [a for a in list_accounts() if a["owner_id"] == owner_id]


def get_account(aid):
    r = db.q1("SELECT * FROM accounts WHERE id=?", (aid,))
    return _account(r, {aid: _schedules_of(aid)}) if r else None


def count_accounts(owner_id=None):
    if owner_id is None:
        return db.q1("SELECT COUNT(*) c FROM accounts")["c"]
    return db.q1("SELECT COUNT(*) c FROM accounts WHERE owner_id=?", (owner_id,))["c"]


def save_account(acc):
    with db.tx():
        db.x("INSERT INTO accounts(id, owner_id, name, created_at) VALUES(?,?,?,?) "
             "ON CONFLICT(id) DO UPDATE SET owner_id=excluded.owner_id, name=excluded.name",
             (acc["id"], acc.get("owner_id"), acc["name"], acc.get("created_at") or now_iso()))
        db.x("DELETE FROM schedules WHERE account_id=?", (acc["id"],))
        for i, s in enumerate(acc.get("schedules") or []):
            c = s.get("contacts")
            db.x("INSERT INTO schedules(id, account_id, time, enabled, message, contacts_json, position) VALUES(?,?,?,?,?,?,?)",
                 (s["id"], acc["id"], s["time"], 1 if s.get("enabled", True) else 0, s.get("message") or "",
                  None if c is None else _j(c), i))


def create_account(name, owner_id=None):
    acc = {"id": uuid.uuid4().hex[:6], "name": name, "owner_id": owner_id, "schedules": [], "created_at": now_iso()}
    save_account(acc)
    return acc


def delete_account(aid):
    with db.tx():
        db.x("DELETE FROM accounts WHERE id=?", (aid,))  # kontak, jadwal, cookie, convs ikut terhapus (CASCADE)
    shutil.rmtree(os.path.join(DATA_DIR, "accounts", aid), ignore_errors=True)


def _dedupe_ci(items):
    seen, out = set(), []
    for c in items:
        if c.lower() not in seen:
            seen.add(c.lower())
            out.append(c)
    return out


# ---------------------------------------------------- adapter data per akun
class _State:
    def __init__(self, aid):
        self.aid = aid

    def _ensure(self):
        db.x("INSERT OR IGNORE INTO account_state(account_id) VALUES(?)", (self.aid,))


class CookiesStore(_State):
    def read(self):
        r = db.q1("SELECT cookies_enc FROM account_state WHERE account_id=?", (self.aid,))
        if not r or r["cookies_enc"] is None:
            return []
        return json.loads(crypto.decrypt(r["cookies_enc"]))

    def write(self, cookies):
        with db.tx():
            self._ensure()
            db.x("UPDATE account_state SET cookies_enc=?, cookies_updated_at=? WHERE account_id=?",
                 (crypto.encrypt(_j(cookies)), datetime.now().timestamp(), self.aid))

    def delete(self):
        with db.tx():
            self._ensure()
            db.x("UPDATE account_state SET cookies_enc=NULL, cookies_updated_at=NULL WHERE account_id=?", (self.aid,))


class ContactsStore(_State):
    def read(self):
        return [r["name"] for r in db.q("SELECT name FROM contacts WHERE account_id=? ORDER BY position", (self.aid,))]

    def write(self, names):
        with db.tx():
            db.x("DELETE FROM contacts WHERE account_id=?", (self.aid,))
            for i, n in enumerate(_dedupe_ci(names)):
                db.x("INSERT INTO contacts(account_id, name, position) VALUES(?,?,?)", (self.aid, n, i))


class MetaStore(_State):
    def read(self):
        r = db.q1("SELECT meta_json FROM account_state WHERE account_id=?", (self.aid,))
        return json.loads(r["meta_json"]) if r and r["meta_json"] else {}

    def write(self, meta):
        with db.tx():
            self._ensure()
            status = "invalid" if meta.get("invalid") else ("ok" if meta.get("last_ok") else None)
            db.x("UPDATE account_state SET meta_json=?, last_check=?, cookie_status=? WHERE account_id=?",
                 (_j(meta), meta.get("last_check"), status, self.aid))


class ConvsStore(_State):
    def read(self):
        return {r["name_lc"]: r["conv_id"] for r in db.q("SELECT name_lc, conv_id FROM convs WHERE account_id=?", (self.aid,))}

    def write(self, d):
        with db.tx():
            db.x("DELETE FROM convs WHERE account_id=?", (self.aid,))
            for k, v in d.items():
                db.x("INSERT INTO convs(account_id, name_lc, conv_id) VALUES(?,?,?)", (self.aid, k, v))


class AccountStores:
    def __init__(self, aid):
        self.cookies, self.contacts = CookiesStore(aid), ContactsStore(aid)
        self.meta, self.convs = MetaStore(aid), ConvsStore(aid)


def stores(aid):
    return AccountStores(aid)


def rename_contact(aid, old, new):
    """Ganti nama kontak di daftar, di jadwal yang memilihnya, dan di pemetaan ID percakapan."""
    st = stores(aid)
    lo, ln = old.strip().lower(), new.strip().lower()
    with db.tx():
        st.contacts.write(_dedupe_ci([new if c.lower() == lo else c for c in st.contacts.read()]))
        acc = get_account(aid)
        if acc:
            for sched in acc["schedules"]:
                if sched.get("contacts") is not None:
                    sched["contacts"] = _dedupe_ci([new if c.lower() == lo else c for c in sched["contacts"]])
            save_account(acc)
        convs = st.convs.read()
        if lo in convs and lo != ln:
            convs[ln] = convs.pop(lo)
            st.convs.write(convs)


# ------------------------------------------------------------ pengguna
def _user(r):
    if not r:
        return None
    notify = {}
    if r["notify_json"]:
        try:
            notify = json.loads(crypto.decrypt(r["notify_json"]))
        except Exception:  # noqa: BLE001
            notify = {}
    return {"id": r["id"], "username": r["username"], "pw_hash": r["pw_hash"], "salt": r["salt"], "iterations": r["iterations"],
            "role": r["role"], "disabled": bool(r["disabled"]), "created_at": r["created_at"],
            "pw_changed_at": r["pw_changed_at"], "notify": notify}


def users_all():
    return [_user(r) for r in db.q("SELECT * FROM users ORDER BY created_at, rowid")]


def user_get(uid):
    return _user(db.q1("SELECT * FROM users WHERE id=?", (uid,)))


def user_by_name(name):
    return _user(db.q1("SELECT * FROM users WHERE username=?", ((name or "").strip().lower(),)))


def users_count():
    return db.q1("SELECT COUNT(*) c FROM users")["c"]


def user_save(u):
    nj = crypto.encrypt(_j(u.get("notify") or {})) if u.get("notify") else None
    db.x("INSERT INTO users(id, username, pw_hash, salt, iterations, role, disabled, created_at, pw_changed_at, notify_json) "
         "VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET username=excluded.username, pw_hash=excluded.pw_hash, "
         "salt=excluded.salt, iterations=excluded.iterations, role=excluded.role, disabled=excluded.disabled, "
         "pw_changed_at=excluded.pw_changed_at, notify_json=excluded.notify_json",
         (u["id"], u["username"], u["pw_hash"], u["salt"], u["iterations"], u["role"], 1 if u.get("disabled") else 0,
          u.get("created_at"), u.get("pw_changed_at"), nj))


def user_delete(uid):
    db.x("DELETE FROM users WHERE id=?", (uid,))


# -------------------------------------------------------------- sesi login
def session_put(token_hash, user_id, created, expires):
    with db.tx():
        db.x("DELETE FROM sessions WHERE expires_at<?", (datetime.now().timestamp(),))
        db.x("INSERT OR REPLACE INTO sessions(token_hash, user_id, created_at, expires_at) VALUES(?,?,?,?)",
             (token_hash, user_id, created, expires))


def session_get(token_hash):
    r = db.q1("SELECT user_id, expires_at FROM sessions WHERE token_hash=?", (token_hash,))
    return {"user_id": r["user_id"], "expires": r["expires_at"]} if r else None


def session_del(token_hash):
    db.x("DELETE FROM sessions WHERE token_hash=?", (token_hash,))


def sessions_del_user(user_id, keep_hash=None):
    db.x("DELETE FROM sessions WHERE user_id=? AND token_hash IS NOT ?", (user_id, keep_hash))


# ------------------------------------------------------------------ riwayat
def _run(r, logs=True):
    out = {"id": r["id"], "account": {"id": r["account_id"], "name": r["account_name"]}, "owner_id": r["owner_id"],
           "mode": r["mode"], "trigger": r["trigger"], "by": r["run_by"], "label": r["label"], "status": r["status"],
           "started_at": r["started_at"], "finished_at": r["finished_at"], "sent": r["sent"] or 0, "total": r["total"] or 0,
           "error": r["error"], "message": r["message"], "results": json.loads(r["results_json"] or "[]")}
    if logs:
        out["logs"] = json.loads(r["logs_json"] or "[]")
    return out


def new_run_id():
    """ID run 8 hex (dipakai juga untuk folder bukti); dipastikan belum dipakai agar tidak menimpa riwayat."""
    while True:
        rid = uuid.uuid4().hex[:8]
        if not db.q1("SELECT 1 FROM runs WHERE id=?", (rid,)):
            return rid


def insert_run(run):
    acc = run.get("account") or {}
    with db.tx():
        db.x("INSERT OR REPLACE INTO runs(id, account_id, owner_id, account_name, mode, trigger, run_by, label, status, "
             "started_at, finished_at, sent, total, error, message, results_json, logs_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
             (run["id"], acc.get("id"), run.get("owner_id"), acc.get("name"), run.get("mode"), run.get("trigger"), run.get("by"),
              run.get("label"), run.get("status"), run.get("started_at"), run.get("finished_at"), run.get("sent", 0),
              run.get("total", 0), run.get("error"), run.get("message"), _j(run.get("results", [])), _j(run.get("logs", []))))
    return prune_runs(acc.get("id"))


def get_run(rid):
    r = db.q1("SELECT * FROM runs WHERE id=?", (rid,))
    return _run(r) if r else None


def _scope(owner_id, account_id, mode, status):
    where, args = [], []
    if account_id:
        where.append("account_id=?")
        args.append(account_id)
    else:
        where.append("owner_id=?")
        args.append(owner_id)
    if mode:
        where.append("mode=?")
        args.append(mode)
    if status:
        where.append("status=?")
        args.append(status)
    return " AND ".join(where), args


def query_runs(owner_id, account_id=None, page=1, page_size=20, mode=None, status=None):
    """Riwayat milik satu pengguna (atau satu akunnya), terbaru dulu. Return (items, total)."""
    w, a = _scope(owner_id, account_id, mode, status)
    total = db.q1(f"SELECT COUNT(*) c FROM runs WHERE {w}", a)["c"]
    rows = db.q(f"SELECT * FROM runs WHERE {w} ORDER BY started_at DESC LIMIT ? OFFSET ?", a + [page_size, (page - 1) * page_size])
    return [_run(r) for r in rows], total


def last_run(owner_id):
    r = db.q1("SELECT * FROM runs WHERE owner_id=? ORDER BY started_at DESC LIMIT 1", (owner_id,))
    return _run(r) if r else None


def runs_since(account_id, since_iso, mode="send"):
    rows = db.q("SELECT * FROM runs WHERE account_id=? AND mode=? AND started_at>=? ORDER BY started_at DESC",
                (account_id, mode, since_iso))
    return [_run(r, logs=False) for r in rows]


def day_stats(account_id, since_day, mode="send"):
    """Ringkasan per hari: {day: {runs, sent, total, full}} untuk run yang sudah selesai."""
    out = {}
    for r in db.q("SELECT substr(started_at,1,10) d, COUNT(*) n, SUM(sent) s, SUM(total) t, "
                  "SUM(CASE WHEN total>0 AND sent>=total THEN 1 ELSE 0 END) f FROM runs "
                  "WHERE account_id=? AND mode=? AND status NOT IN ('running','expired','cancelled') AND substr(started_at,1,10)>=? GROUP BY d",
                  (account_id, mode, since_day)):
        out[r["d"]] = {"runs": r["n"], "sent": r["s"] or 0, "total": r["t"] or 0, "full": r["f"] or 0}
    return out


def last_success_at(account_id):
    """Waktu mulai kiriman sukses terakhir (sent > 0) untuk akun ini, atau None."""
    r = db.q1("SELECT MAX(started_at) t FROM runs WHERE account_id=? AND mode='send' AND sent>0", (account_id,))
    return r["t"] if r else None


def send_days(account_id, since_day):
    return [r["d"] for r in db.q("SELECT DISTINCT substr(started_at,1,10) d FROM runs WHERE account_id=? AND mode='send' "
                                 "AND sent>0 AND substr(started_at,1,10)>=? ORDER BY d DESC", (account_id, since_day))]


def prune_runs(account_id):
    """Terapkan retensi (HISTORY_DAYS dan HISTORY_PER_ACCOUNT) untuk satu akun; return id run yang dihapus."""
    if not account_id:
        return []
    cutoff = (datetime.now() - timedelta(days=config.HISTORY_DAYS)).isoformat(timespec="seconds")
    ids = [r["id"] for r in db.q("SELECT id FROM runs WHERE account_id=? AND started_at<?", (account_id, cutoff))]
    ids += [r["id"] for r in db.q("SELECT id FROM runs WHERE account_id=? ORDER BY started_at DESC LIMIT -1 OFFSET ?",
                                  (account_id, config.HISTORY_PER_ACCOUNT))]
    ids = list(dict.fromkeys(ids))
    if ids:
        with db.tx():
            for i in range(0, len(ids), 500):
                chunk = ids[i:i + 500]
                db.x(f"DELETE FROM runs WHERE id IN ({','.join('?' * len(chunk))})", chunk)
        remove_proofs(ids)
    return ids


def remove_proofs(run_ids):
    base = os.path.join(DATA_DIR, "proofs")
    for rid in run_ids:
        shutil.rmtree(os.path.join(base, rid), ignore_errors=True)


def delete_runs(account_ids=None, owner_id=None):
    """Hapus riwayat (dan bukti) milik akun-akun tertentu atau seorang pemilik."""
    if account_ids is not None:
        ids = []
        for aid in account_ids:
            ids += [r["id"] for r in db.q("SELECT id FROM runs WHERE account_id=?", (aid,))]
    else:
        ids = [r["id"] for r in db.q("SELECT id FROM runs WHERE owner_id=?", (owner_id,))]
    with db.tx():
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            db.x(f"DELETE FROM runs WHERE id IN ({','.join('?' * len(chunk))})", chunk)
    remove_proofs(ids)
    return len(ids)


# ----------------------------------------------------------------- migrasi
from . import migrate_json  # noqa: E402

migrate_json.run()
