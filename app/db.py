"""SQLite (WAL) untuk seluruh data panel: koneksi per thread, transaksi, dan migrasi skema."""
import os
import sqlite3
import threading
from contextlib import contextmanager

from . import config

_local = threading.local()
_init_lock = threading.Lock()
_ready = set()


def db_path():
    return os.path.join(config.DATA_DIR, "streak.db")


def conn():
    path = db_path()
    c = getattr(_local, "conn", None)
    if c is None or getattr(_local, "path", None) != path:
        init()
        os.makedirs(config.DATA_DIR, exist_ok=True)
        c = sqlite3.connect(path, timeout=5, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA busy_timeout=5000")
        c.execute("PRAGMA synchronous=NORMAL")
        _local.conn, _local.path, _local.depth = c, path, 0
    return c


def q(sql, args=()):
    return conn().execute(sql, args).fetchall()


def q1(sql, args=()):
    return conn().execute(sql, args).fetchone()


def x(sql, args=()):
    return conn().execute(sql, args)


@contextmanager
def tx():
    """Transaksi tulis (BEGIN IMMEDIATE); bersarang ikut transaksi terluar."""
    c = conn()
    if _local.depth:
        _local.depth += 1
        try:
            yield c
        finally:
            _local.depth -= 1
        return
    c.execute("BEGIN IMMEDIATE")
    _local.depth = 1
    try:
        yield c
        c.execute("COMMIT")
    except BaseException:
        c.execute("ROLLBACK")
        raise
    finally:
        _local.depth = 0


# ----------------------------------------------------------------- migrasi
def _script(c, sql):
    """Jalankan banyak pernyataan DDL di dalam transaksi yang sedang berjalan."""
    for stmt in sql.split(";"):
        if stmt.strip():
            c.execute(stmt)


def _m1(c):
    _script(c, """
    CREATE TABLE users(
      id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, pw_hash TEXT NOT NULL, salt TEXT NOT NULL,
      iterations INTEGER NOT NULL, role TEXT NOT NULL, disabled INTEGER NOT NULL DEFAULT 0,
      created_at TEXT, pw_changed_at TEXT, notify_json BLOB);
    CREATE TABLE sessions(
      token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      created_at REAL, expires_at REAL NOT NULL);
    CREATE INDEX sessions_user ON sessions(user_id);
    CREATE TABLE settings(key TEXT PRIMARY KEY, value_json TEXT);
    CREATE TABLE accounts(
      id TEXT PRIMARY KEY, owner_id TEXT REFERENCES users(id) ON DELETE CASCADE, name TEXT NOT NULL, created_at TEXT);
    CREATE UNIQUE INDEX accounts_owner_name ON accounts(owner_id, lower(name));
    CREATE INDEX accounts_owner ON accounts(owner_id);
    CREATE TABLE schedules(
      id TEXT NOT NULL, account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
      time TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, message TEXT NOT NULL DEFAULT '',
      contacts_json TEXT, position INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(account_id, id));
    CREATE TABLE contacts(
      account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE, name TEXT NOT NULL, position INTEGER NOT NULL DEFAULT 0);
    CREATE UNIQUE INDEX contacts_uq ON contacts(account_id, lower(name));
    CREATE TABLE convs(
      account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE, name_lc TEXT NOT NULL, conv_id TEXT,
      PRIMARY KEY(account_id, name_lc));
    CREATE TABLE account_state(
      account_id TEXT PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE, cookies_enc BLOB, cookies_updated_at REAL,
      last_check REAL, cookie_status TEXT, meta_json TEXT);
    CREATE TABLE runs(
      id TEXT PRIMARY KEY, account_id TEXT, owner_id TEXT, account_name TEXT, mode TEXT, trigger TEXT, run_by TEXT,
      label TEXT, status TEXT, started_at TEXT, finished_at TEXT, sent INTEGER DEFAULT 0, total INTEGER DEFAULT 0,
      error TEXT, message TEXT, results_json TEXT, logs_json TEXT);
    CREATE INDEX runs_owner_started ON runs(owner_id, started_at DESC);
    CREATE INDEX runs_account_started ON runs(account_id, started_at DESC);
    CREATE INDEX runs_status ON runs(status);
    """)


MIGRATIONS = [_m1]


def init():
    path = db_path()
    if path in _ready:
        return
    with _init_lock:
        if path in _ready:
            return
        os.makedirs(config.DATA_DIR, exist_ok=True)
        c = sqlite3.connect(path, timeout=5, isolation_level=None)
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA busy_timeout=5000")
        ver = c.execute("PRAGMA user_version").fetchone()[0]
        for i, fn in enumerate(MIGRATIONS[ver:], start=ver + 1):
            c.execute("BEGIN IMMEDIATE")
            try:
                fn(c)
                c.execute(f"PRAGMA user_version={i}")
                c.execute("COMMIT")
            except BaseException:
                c.execute("ROLLBACK")
                raise
        c.close()
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        _ready.add(path)
