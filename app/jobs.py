"""Antrean job browser yang disimpan di SQLite (send / check / test)."""
import json
import sqlite3
import time
import uuid

from . import db

ACTIVE = ("queued", "running")


class Duplicate(Exception):
    """Sudah ada job aktif (antre/berjalan) untuk akun dan jenis yang sama."""


def _row(r):
    if not r:
        return None
    d = dict(r)
    d["contacts"] = json.loads(d.pop("contacts_json")) if d.get("contacts_json") is not None else None
    d["by"] = d.pop("run_by", None)
    return d


def enqueue(account_id, owner_id, kind, trigger, label=None, message=None, contacts=None, priority=None, due_at=None, by=None):
    if priority is None:
        priority = 2 if trigger == "keepalive" else (0 if trigger == "manual" else 1)
    now = time.time()
    jid = uuid.uuid4().hex[:10]
    try:
        db.x("INSERT INTO jobs(id, account_id, owner_id, kind, trigger, run_by, label, message, contacts_json, priority, due_at, enqueued_at, status) "
             "VALUES(?,?,?,?,?,?,?,?,?,?,?,?, 'queued')",
             (jid, account_id, owner_id, kind, trigger, by, label, message, None if contacts is None else json.dumps(contacts, ensure_ascii=False),
              priority, due_at or now, now))
    except sqlite3.IntegrityError as e:
        raise Duplicate() from e
    return get(jid)


def get(jid):
    return _row(db.q1("SELECT * FROM jobs WHERE id=?", (jid,)))


def queued():
    """Job antre dalam urutan eksekusi: prioritas, lalu waktu jatuh tempo, lalu waktu masuk."""
    return [_row(r) for r in db.q("SELECT * FROM jobs WHERE status='queued' ORDER BY priority, due_at, enqueued_at")]


def running():
    return [_row(r) for r in db.q("SELECT * FROM jobs WHERE status='running' ORDER BY started_at")]


def of_owner(owner_id):
    return [_row(r) for r in db.q("SELECT * FROM jobs WHERE owner_id=? AND status IN ('queued','running') ORDER BY priority, due_at", (owner_id,))]


def active_for(account_id, kind=None):
    if kind:
        return _row(db.q1("SELECT * FROM jobs WHERE account_id=? AND kind=? AND status IN ('queued','running')", (account_id, kind)))
    return _row(db.q1("SELECT * FROM jobs WHERE account_id=? AND status IN ('queued','running')", (account_id,)))


def counts():
    r = {x["status"]: x["c"] for x in db.q("SELECT status, COUNT(*) c FROM jobs WHERE status IN ('queued','running') GROUP BY status")}
    return {"queued": r.get("queued", 0), "running": r.get("running", 0)}


def claim(jid):
    """Tandai job berjalan bila masih antre. Return True bila berhasil diambil."""
    with db.tx():
        c = db.x("UPDATE jobs SET status='running', started_at=? WHERE id=? AND status='queued'", (time.time(), jid))
        return c.rowcount == 1


def finish(jid, status, run_id=None, reason=None):
    db.x("UPDATE jobs SET status=?, run_id=COALESCE(?, run_id), reason=?, finished_at=? WHERE id=?",
         (status, run_id, reason, time.time(), jid))


def set_run(jid, run_id):
    db.x("UPDATE jobs SET run_id=? WHERE id=?", (run_id, jid))


def cancel_queued(jid, owner_id=None):
    q = "UPDATE jobs SET status='cancelled', finished_at=?, reason='Dibatalkan' WHERE id=? AND status='queued'"
    args = [time.time(), jid]
    if owner_id is not None:
        q += " AND owner_id=?"
        args.append(owner_id)
    return db.x(q, args).rowcount == 1


def drop_account(account_id):
    db.x("DELETE FROM jobs WHERE account_id=?", (account_id,))


def recover(window_seconds):
    """Setelah restart: job 'running' kembali antre bila masih dalam jendela, selain itu kedaluwarsa."""
    now = time.time()
    back, gone = [], []
    for r in db.q("SELECT * FROM jobs WHERE status='running'"):
        j = _row(r)
        if j["trigger"] == "schedule" and now - j["due_at"] > window_seconds:
            gone.append(j)
        elif j["trigger"] != "schedule" and now - j["enqueued_at"] > 600:
            gone.append(j)
        else:
            back.append(j)
    with db.tx():
        for j in back:
            db.x("UPDATE jobs SET status='queued', started_at=NULL WHERE id=?", (j["id"],))
        for j in gone:
            db.x("UPDATE jobs SET status='expired', finished_at=?, reason='Server Dimulai Ulang' WHERE id=?", (now, j["id"]))
    return back, gone


def overdue(window_seconds):
    """Job terjadwal yang masih antre tetapi jendelanya sudah lewat."""
    cutoff = time.time() - window_seconds
    return [_row(r) for r in db.q("SELECT * FROM jobs WHERE status='queued' AND trigger='schedule' AND due_at<?", (cutoff,))]


def prune(older_days=7):
    db.x("DELETE FROM jobs WHERE status NOT IN ('queued','running') AND finished_at<?", (time.time() - older_days * 86400,))
