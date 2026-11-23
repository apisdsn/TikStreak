import hashlib
import json
import logging
import os
import re
from datetime import datetime, timedelta
import secrets
import time
import uuid
import threading
from typing import List, Optional
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config
from .auth import (
    COOKIE,
    LEGACY_COOKIE,
    accessible_ids,
    can_access,
    current_user,
    owner_for_new,
    public_user,
    require_admin,
    router as auth_router,
    session_token,
    set_cookie,
    user_from_token,
    users_count,
    visible_accounts,
)
from .cookies import parse_cookies, summary
from .messages import MAX_LENGTH, MAX_VARIATIONS
from .streaks import effective_streak
from . import db, jobs, migrate_json
from .login import login_mgr
from .notify import DISCORD_RE, send_discord, send_telegram
from .runner import runner
from .store import (
    DEFAULT_SETTINGS,
    create_account,
    delete_account,
    get_account,
    get_settings,
    count_accounts,
    delete_runs,
    get_run,
    last_run as store_last_run,
    day_stats,
    query_runs,
    runs_since,
    SCAN_TTL,
    contact_stats,
    save_settings,
    scan_clear,
    scan_get,
    send_days,
    list_accounts,
    rename_contact,
    save_account,
    stores,
)

if not config.API_KEY:
    raise SystemExit("API_KEY belum diatur. Isi API_KEY pada file .env")

app = FastAPI(title="Bara", docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(auth_router)
STATIC = os.path.join(os.path.dirname(__file__), "static")


auth = current_user


def resolve_account(user, account_id):
    """Akun milik/diizinkan untuk pemanggil; 404 bila tidak ada atau bukan haknya."""
    accs = visible_accounts(user)
    if not account_id:
        if not accs:
            raise HTTPException(404, "Akun Tidak Ditemukan")
        return accs[0]
    found = next((a for a in accs if a["id"] == account_id), None)
    if not found:
        raise HTTPException(404, "Akun Tidak Ditemukan")
    return found


def acct(account: Optional[str] = Query(None), user=Depends(current_user)):
    """Akun yang dipilih lewat ?account=ID (default: akun pertama yang boleh diakses)."""
    return resolve_account(user, account)


@app.on_event("startup")
def _startup():
    runner.start_workers()
    old = migrate_json.backup_dirs()
    if old:
        logging.getLogger("bara").warning("Cadangan JSON lama berisi cookie plaintext masih ada (%d folder di %s). Hapus lewat Pengaturan "
                                          "atau hapus folder backup-json-* setelah yakin.", len(old), config.DATA_DIR)


@app.on_event("shutdown")
def _shutdown():
    runner.shutdown()


# ---------------------------------------------------------------- schemas
class ScheduleIn(BaseModel):
    id: Optional[str] = None
    enabled: bool = True
    time: str
    message: str = ""
    contacts: Optional[List[str]] = None  # None = semua kontak akun


class SettingsIn(BaseModel):
    message: Optional[str] = None
    timezone: Optional[str] = None
    telegram_enabled: Optional[bool] = None
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    discord_enabled: Optional[bool] = None
    discord_webhook: Optional[str] = None
    notify_screenshot: Optional[bool] = None
    keepalive_enabled: Optional[bool] = None
    keepalive_hours: Optional[int] = None
    page_load_wait: Optional[int] = None
    element_wait: Optional[int] = None
    send_delay: Optional[int] = None
    retry_enabled: Optional[bool] = None
    retry_delay_min: Optional[int] = None
    retry_max: Optional[int] = None


class AccountIn(BaseModel):
    name: Optional[str] = None
    schedules: Optional[List[ScheduleIn]] = None
    variations: Optional[List[str]] = None
    random_emoji: Optional[bool] = None


class ContactsIn(BaseModel):
    names: str


class RenameIn(BaseModel):
    old: str
    new: str


class CookiesIn(BaseModel):
    raw: str


class RunIn(BaseModel):
    mode: str = "send"
    message: Optional[str] = None
    account: Optional[str] = None
    contacts: Optional[list[str]] = None  # kirim ulang hanya untuk kontak ini (mode send)


def public_settings():
    s = get_settings()
    token = s.pop("telegram_token")
    s["telegram_token_set"] = bool(token)
    s["discord_webhook_set"] = bool(s.pop("discord_webhook"))
    s["timezone_default"] = config.DEFAULT_TZ
    s["timezone"] = s["timezone"] or config.DEFAULT_TZ
    return s


def run_view(run, with_logs=False):
    if not run:
        return None
    keys = ("id", "account", "mode", "trigger", "by", "label", "status", "started_at", "finished_at", "sent", "total", "error")
    out = {k: run.get(k) for k in keys}
    out["results"] = run.get("results", [])
    if with_logs:
        out["logs"] = run.get("logs", [])
    return out


# -------------------------------------------------------------------- API
@app.get("/api/health")
def health(deep: int = Query(0)):
    if not deep:
        return {"status": "ok"}
    ok, info = runner.deep_health()
    return JSONResponse(info, status_code=200 if ok else 503)


def keepalive_next(aid):
    """Jam (HH:MM, waktu server) pengecekan cookie otomatis berikutnya, atau None."""
    s = get_settings()
    st = stores(aid)
    if not s["keepalive_enabled"] or not st.cookies.read():
        return None
    ts = max(st.meta.read().get("last_check", 0) + s["keepalive_hours"] * 3600, time.time())
    return datetime.fromtimestamp(ts).strftime("%H:%M")


def account_view(acc, user=None):
    st = stores(acc["id"])
    return {
        "id": acc["id"],
        "name": acc["name"],
        "contacts": len(st.contacts.read()),
        "cookies": cookie_view(acc["id"]),
        "schedules": acc["schedules"],
        "variations": acc.get("variations", []),
        "random_emoji": bool(acc.get("random_emoji")),
        "next_run": runner.next_run_at(acc["id"]),
        "next": runner.next_schedule(acc["id"]),
        "keepalive_next": keepalive_next(acc["id"]),
    }


def _my_login(user):
    s = login_mgr.session_for(user["id"])
    return s


@app.get("/api/status")
def status(user=Depends(current_user)):
    ids = accessible_ids(user)
    last = store_last_run(user["id"])
    mine_running = runner.running_runs(ids)
    cur = mine_running[0] if mine_running else None
    q = runner.view_for(user["id"])
    s_login = _my_login(user)
    return {
        "running": bool(mine_running),
        "current": run_view(cur) if cur else None,
        "queue": q,
        "last_run": run_view(last, with_logs=True) if last else None,
        "accounts": [account_view(a, user) for a in visible_accounts(user)],
        "login": s_login.account_id if s_login.active else None,
        "server_now": datetime.now().isoformat(timespec="seconds"),
        "user": public_user(user),
    }


@app.get("/api/settings", dependencies=[Depends(current_user)])
def read_settings():
    return public_settings()


@app.put("/api/settings", dependencies=[Depends(require_admin)])
def write_settings(body: SettingsIn):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if data.get("timezone"):
        try:
            ZoneInfo(data["timezone"])
        except Exception:
            raise HTTPException(400, "Timezone Tidak Dikenal")
    if "message" in data and not data["message"].strip():
        raise HTTPException(400, "Pesan Tidak Boleh Kosong")
    if "keepalive_hours" in data and not 1 <= data["keepalive_hours"] <= 72:
        raise HTTPException(400, "Interval Penyegaran Harus 1-72 Jam")
    for k in ("page_load_wait", "element_wait", "send_delay"):
        if k in data and not 0 <= data[k] <= 60:
            raise HTTPException(400, f"{k} Harus 0-60 Detik")
    if "retry_delay_min" in data and not 1 <= data["retry_delay_min"] <= 240:
        raise HTTPException(400, "Jeda Kirim Ulang Harus 1-240 Menit")
    if "retry_max" in data and not 0 <= data["retry_max"] <= 5:
        raise HTTPException(400, "Percobaan Ulang Harus 0-5 Kali")
    for k in ("telegram_token", "discord_webhook"):
        if data.get(k) == "":
            data.pop(k)
    if "discord_webhook" in data and data["discord_webhook"] != "-" and not DISCORD_RE.match(data["discord_webhook"]):
        raise HTTPException(400, "URL Webhook Discord Tidak Valid")
    if data.get("discord_webhook") == "-":  # hapus webhook
        data["discord_webhook"] = ""
    merged = {**get_settings(), **data}
    save_settings({k: merged[k] for k in DEFAULT_SETTINGS})
    return public_settings()


@app.post("/api/telegram/test", dependencies=[Depends(require_admin)])
def telegram_test():
    ok, err = send_telegram(get_settings(), "✅ Tes Notifikasi dari Bara")
    if not ok:
        raise HTTPException(400, err)
    return {"ok": True}


@app.post("/api/discord/test", dependencies=[Depends(require_admin)])
def discord_test():
    ok, err = send_discord(get_settings(), "✅ Tes Notifikasi dari Bara")
    if not ok:
        raise HTTPException(400, err)
    return {"ok": True}


def clean_schedules(items):
    if len(items) > 8:
        raise HTTPException(400, "Maksimal 8 Jadwal per Akun")
    clean, seen = [], set()
    for x in items:
        x = x.model_dump()
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", x["time"]):
            raise HTTPException(400, "Format Jam Harus HH:MM")
        if len(x["message"]) > 500:
            raise HTTPException(400, "Pesan Jadwal Maksimal 500 Karakter")
        sid = x["id"] if x.get("id") and x["id"] not in seen else uuid.uuid4().hex[:6]
        seen.add(sid)
        contacts = x.get("contacts")
        if contacts is not None:
            contacts = list(dict.fromkeys(c.strip() for c in contacts if c.strip()))[:200]
            if not contacts:
                raise HTTPException(400, f"Jadwal {x['time']}: Pilih Minimal Satu Kontak atau Pilih Semua Kontak")
        clean.append({"id": sid, "enabled": bool(x["enabled"]), "time": x["time"],
                      "message": x["message"].strip(), "contacts": contacts})
    return clean


def clean_name(name, owner_id, exclude_id=None):
    name = (name or "").strip()
    if not 1 <= len(name) <= 40:
        raise HTTPException(400, "Nama Akun 1-40 Karakter")
    taken = {a["name"].lower() for a in list_accounts() if a.get("owner_id") == owner_id and a["id"] != exclude_id}
    if name.lower() in taken:
        raise HTTPException(400, "Nama Akun Sudah Dipakai")
    return name


@app.get("/api/accounts")
def accounts(user=Depends(current_user)):
    return {"accounts": [account_view(a, user) for a in visible_accounts(user)]}


@app.post("/api/accounts")
def add_account(body: AccountIn, user=Depends(current_user)):
    owner = owner_for_new(user)
    if count_accounts() >= config.MAX_ACCOUNTS:
        raise HTTPException(400, f"Maksimal {config.MAX_ACCOUNTS} Akun")
    cap = config.MAX_ACCOUNTS_PER_ADMIN if user["role"] == "admin" else config.MAX_ACCOUNTS_PER_USER
    if owner is None:
        raise HTTPException(400, "Belum Ada Admin: Selesaikan Setup Dulu")
    if count_accounts(owner) >= cap:
        raise HTTPException(400, f"Maksimal {cap} Akun per Pengguna")
    acc = create_account(clean_name(body.name, owner), owner)
    return account_view(acc, user)


@app.put("/api/accounts/{aid}")
def update_account(aid: str, body: AccountIn, user=Depends(current_user)):
    acc = resolve_account(user, aid)
    if body.name is not None and body.name.strip() != acc["name"]:
        acc["name"] = clean_name(body.name, acc.get("owner_id"), aid)
    if body.schedules is not None:
        acc["schedules"] = clean_schedules(body.schedules)
    if body.variations is not None:
        items = [v.strip() for v in body.variations if v and v.strip()]
        if len(items) > MAX_VARIATIONS:
            raise HTTPException(400, f"Maksimal {MAX_VARIATIONS} Variasi Pesan")
        if any(len(v) > MAX_LENGTH for v in items):
            raise HTTPException(400, f"Setiap Variasi Maksimal {MAX_LENGTH} Karakter")
        acc["variations"] = items
    if body.random_emoji is not None:
        acc["random_emoji"] = body.random_emoji
    save_account(acc)
    return account_view(acc, user)


@app.delete("/api/accounts/{aid}")
def remove_account(aid: str, user=Depends(current_user)):
    acc = resolve_account(user, aid)
    mine = [a for a in list_accounts() if a.get("owner_id") == acc.get("owner_id")]
    if len(mine) <= 1:
        raise HTTPException(400, "Minimal Harus Ada Satu Akun")
    if runner.account_busy(aid):
        raise HTTPException(409, "Akun Sedang Dipakai Proses yang Berjalan")
    login_mgr.stop_account(aid)
    jobs.drop_account(aid)
    delete_account(aid)
    delete_runs(account_ids=[aid])
    return {"ok": True}


@app.get("/api/contacts", dependencies=[Depends(current_user)])
def list_contacts(acc=Depends(acct)):
    return {"contacts": stores(acc["id"]).contacts.read()}


@app.post("/api/contacts", dependencies=[Depends(current_user)])
def add_contacts(body: ContactsIn, acc=Depends(acct)):
    contacts_store = stores(acc["id"]).contacts
    current = contacts_store.read()
    seen = {c.lower() for c in current}
    added = []
    for n in re.split(r"[\n,]+", body.names):
        n = n.strip()
        if n and n.lower() not in seen:
            seen.add(n.lower())
            current.append(n)
            added.append(n)
    if not added:
        raise HTTPException(400, "Tidak Ada Kontak Baru (Kosong atau Sudah Ada)")
    contacts_store.write(current)
    return {"contacts": current, "added": added}


class ImportIn(BaseModel):
    ids: list[str]


def _scan_view(acc, user):
    """Status pemindaian kontak untuk akun ini: antre/berjalan, atau hasil terakhir (kedaluwarsa 1 jam)."""
    job = next((j for j in runner.view_for(user["id"])["mine"] if j["account_id"] == acc["id"] and j["kind"] == "scan_contacts"), None)
    if job:
        return {"state": job["state"], "position": job["position"], "eta": job["eta"], "job_id": job["id"], "items": [], "error": None}
    res = scan_get(acc["id"])
    if not res:
        return {"state": "none", "items": [], "error": None}
    existing = {c.lower() for c in stores(acc["id"]).contacts.read()}
    items = [{**i, "exists": i["nick"].lower() in existing} for i in res["items"]]
    return {"state": "failed" if res.get("error") else "done", "items": items, "error": res.get("error"), "expires_in": max(0, int(SCAN_TTL - (time.time() - res["at"])))}


def _contact_rows(acc):
    """Status hari ini per kontak: streak, kiriman terakhir, dan state (sent/failed/pending/unscheduled)."""
    today = datetime.now().date().isoformat()
    stats = contact_stats(acc["id"])
    sched = [s for s in acc["schedules"] if s["enabled"]]
    rows = []
    for name in stores(acc["id"]).contacts.read():
        s = stats.get(name.lower())
        if s and (s["last_ok_at"] or "")[:10] == today:
            state = "sent"
        elif s and (s["last_fail_at"] or "")[:10] == today:
            state = "failed"
        elif any(x.get("contacts") is None or name.lower() in {c.lower() for c in x["contacts"]} for x in sched):
            state = "pending"
        else:
            state = "unscheduled"
        rows.append({"name": name, "streak": effective_streak(s, today), "last_ok_at": s["last_ok_at"] if s else None,
                     "last_fail_at": s["last_fail_at"] if s else None, "last_error": s["last_error"] if s and state == "failed" else None, "today": state})
    return rows


@app.get("/api/contacts/status", dependencies=[Depends(current_user)])
def contacts_status(acc=Depends(acct)):
    return {"contacts": _contact_rows(acc)}


@app.get("/api/contacts/scan")
def scan_status(acc=Depends(acct), user=Depends(current_user)):
    return _scan_view(acc, user)


@app.post("/api/contacts/scan")
def scan_start(acc=Depends(acct), user=Depends(current_user)):
    if login_mgr.account_active(acc["id"]):
        raise HTTPException(409, "Tutup Sesi Login di Tab Cookie Dulu")
    if not stores(acc["id"]).cookies.read():
        raise HTTPException(400, "Cookie TikTok Belum Diatur")
    try:
        jobs.enqueue(acc["id"], user["id"], "scan_contacts", "manual", by=user["username"])
    except jobs.Duplicate:
        raise HTTPException(409, "Pemindaian Kontak Sudah Berjalan untuk Akun Ini")
    scan_clear(acc["id"])
    return _scan_view(acc, user)


@app.post("/api/contacts/import")
def scan_import(body: ImportIn, acc=Depends(acct), user=Depends(current_user)):
    res = scan_get(acc["id"])
    if not res or res.get("error"):
        raise HTTPException(404, "Hasil Pemindaian Sudah Kedaluwarsa, Pindai Ulang")
    by_id = {i["id"]: i for i in res["items"]}
    st = stores(acc["id"])
    current = st.contacts.read()
    seen = {c.lower() for c in current}
    convs = st.convs.read()
    added = []
    for cid in dict.fromkeys(body.ids):
        item = by_id.get(cid)
        if not item or item["nick"].lower() in seen:
            continue
        seen.add(item["nick"].lower())
        current.append(item["nick"])
        convs[item["nick"].lower()] = cid
        added.append(item["nick"])
    if not added:
        raise HTTPException(400, "Tidak Ada Kontak Baru yang Dipilih")
    st.contacts.write(current)
    st.convs.write(convs)
    return {"contacts": current, "added": added}


@app.put("/api/contacts/rename", dependencies=[Depends(current_user)])
def rename_contact_api(body: RenameIn, acc=Depends(acct)):
    old, new = body.old.strip(), body.new.strip()
    current = stores(acc["id"]).contacts.read()
    if old.lower() not in {c.lower() for c in current}:
        raise HTTPException(404, "Kontak Tidak Ditemukan")
    if not new or len(new) > 100:
        raise HTTPException(400, "Nama Baru 1-100 Karakter")
    if new.lower() != old.lower() and new.lower() in {c.lower() for c in current}:
        raise HTTPException(409, "Nama Baru Sudah Ada di Daftar Kontak")
    rename_contact(acc["id"], old, new)
    return {"contacts": stores(acc["id"]).contacts.read()}


@app.delete("/api/contacts", dependencies=[Depends(current_user)])
def delete_contact(name: str = Query(...), acc=Depends(acct)):
    contacts_store = stores(acc["id"]).contacts
    current = contacts_store.read()
    new = [c for c in current if c.lower() != name.lower()]
    if len(new) == len(current):
        raise HTTPException(404, "Kontak Tidak Ditemukan")
    contacts_store.write(new)
    db.x("DELETE FROM contact_stats WHERE account_id=? AND name_lc=?", (acc["id"], name.lower()))
    # Lepaskan kontak yang dihapus dari jadwal yang memilih kontak tertentu
    for sched in acc["schedules"]:
        if sched.get("contacts") is not None:
            sched["contacts"] = [c for c in sched["contacts"] if c.lower() != name.lower()]
    save_account(acc)
    return {"contacts": new}


def cookie_view(aid):
    st = stores(aid)
    meta = st.meta.read()
    return {**summary(st.cookies.read()), **{k: meta.get(k) for k in ("last_ok", "last_saved", "invalid")}}


def reset_cookie_meta(aid):
    meta_store = stores(aid).meta
    meta = meta_store.read()
    for k in ("invalid", "last_alert", "last_check"):
        meta.pop(k, None)
    meta_store.write(meta)


@app.get("/api/cookies", dependencies=[Depends(current_user)])
def cookie_status(acc=Depends(acct)):
    return cookie_view(acc["id"])


@app.put("/api/cookies", dependencies=[Depends(current_user)])
def set_cookies(body: CookiesIn, acc=Depends(acct)):
    try:
        cookies = parse_cookies(body.raw)
    except ValueError as e:
        raise HTTPException(400, str(e))
    stores(acc["id"]).cookies.write(cookies)
    reset_cookie_meta(acc["id"])
    return cookie_view(acc["id"])


@app.delete("/api/cookies", dependencies=[Depends(current_user)])
def clear_cookies(acc=Depends(acct)):
    stores(acc["id"]).cookies.delete()
    return cookie_view(acc["id"])


class LoginInput(BaseModel):
    type: str
    x: float = 0
    y: float = 0
    dx: float = 0
    dy: float = 0
    key: str = ""
    text: str = ""
    action: str = ""
    index: int = 0


def _login_call(fn, *a):
    try:
        return fn(*a)
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Browser Error: {e}")


@app.post("/api/login/start")
def login_start(acc=Depends(acct), user=Depends(current_user)):
    if runner.account_busy(acc["id"]):
        raise HTTPException(409, "Tunggu Proses yang Sedang Berjalan Selesai")
    _login_call(login_mgr.start, user["id"], acc["id"])
    return {"ok": True}


@app.get("/api/login/status")
def login_status(user=Depends(current_user)):
    return _login_call(_my_login(user).status)


@app.get("/api/login/frame")
def login_frame(user=Depends(current_user)):
    s = _my_login(user)
    try:
        data = s.frame()
    except RuntimeError as e:
        if not s.active:  # sesi sudah berakhir: jangan jadikan galat di konsol browser
            return Response(status_code=204)
        raise HTTPException(400, str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Browser Error: {e}")
    return Response(data, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@app.post("/api/login/input")
def login_input(body: LoginInput, user=Depends(current_user)):
    _login_call(_my_login(user).input, body.model_dump())
    return {"ok": True}


@app.post("/api/login/save")
def login_save(user=Depends(current_user)):
    s = _my_login(user)
    aid = s.account_id
    n = _login_call(s.save)
    login_mgr.stop_owner(user["id"])
    reset_cookie_meta(aid)
    return {"saved": n, **cookie_view(aid)}


@app.post("/api/login/stop")
def login_stop(user=Depends(current_user)):
    login_mgr.stop_owner(user["id"])
    return {"ok": True}


@app.post("/api/run")
def run(body: RunIn, user=Depends(current_user)):
    acc = resolve_account(user, body.account)
    if body.mode not in ("send", "test", "check"):
        raise HTTPException(400, "Mode Harus Send, Test, atau Check")
    if login_mgr.account_active(acc["id"]):
        raise HTTPException(409, "Tutup Sesi Login di Tab Cookie Dulu")
    only = None
    if body.contacts is not None:
        if body.mode != "send" or not body.contacts:
            raise HTTPException(400, "Pilih Kontak hanya untuk Mode Send")
        have = {c.lower(): c for c in stores(acc["id"]).contacts.read()}
        only = [have[c.strip().lower()] for c in body.contacts if c.strip().lower() in have]
        if not only:
            raise HTTPException(404, "Kontak Tidak Ditemukan")
    try:
        job = runner.submit(acc, body.mode, user["id"], user["username"], body.message.strip() if body.message else None, contacts=only)
    except jobs.Duplicate:
        raise HTTPException(409, "Sudah Ada Proses untuk Akun Ini di Antrean")
    mine = next((j for j in runner.view_for(user["id"])["mine"] if j["id"] == job["id"]), {})
    return {"job": {k: job[k] for k in ("id", "account_id", "kind", "trigger", "status")}, **mine}


@app.post("/api/run/stop")
def stop(account: Optional[str] = Query(None), user=Depends(current_user)):
    return {"ok": True, "stopped": runner.stop(user["id"], account)}


@app.delete("/api/jobs/{job_id}")
def cancel_job(job_id: str, user=Depends(current_user)):
    if not runner.cancel_job(job_id, user["id"]):
        raise HTTPException(404, "Job Tidak Ditemukan atau Sudah Berjalan")
    return {"ok": True}


@app.get("/api/queue")
def queue_info(user=Depends(current_user)):
    return runner.view_for(user["id"])


@app.get("/api/queue/slots")
def queue_slots(user=Depends(current_user)):
    """Jumlah jadwal aktif seluruh panel per slot 30 menit (hanya hitungan, tanpa nama)."""
    cap = 15 * runner.workers
    return {"slots": runner.load_slots(), "capacity": cap, "busy_at": max(2, int(cap * 0.6)), "workers": runner.workers}


@app.delete("/api/system/json-backups")
def delete_json_backups(user=Depends(require_admin)):
    return {"ok": True, "deleted": migrate_json.delete_backups()}


@app.get("/api/queue/admin")
def queue_admin(user=Depends(require_admin)):
    from .login import login_mgr as lm
    hourly = {}
    for k, v in runner.load_slots().items():
        hourly[k[:2] + ":00"] = hourly.get(k[:2] + ":00", 0) + v
    return {**jobs.counts(), "workers": runner.workers, "login_sessions": lm.count(), "login_limit": config.LOGIN_SESSIONS,
            "load_by_hour": dict(sorted(hourly.items())), "json_backups": len(migrate_json.backup_dirs())}


@app.get("/api/run/current")
def current(since: int = 0, user=Depends(current_user)):
    mine = runner.running_runs(accessible_ids(user))
    if not mine:
        return {"run": None, "logs": [], "next": 0, "running": False}
    cur = mine[0]
    logs = cur["logs"]
    return {"run": run_view(cur), "logs": logs[since:], "next": len(logs), "running": True}


@app.get("/api/run/screenshot")
def run_screenshot(user=Depends(current_user)):
    from .bot import SHOT_META_PATH, SHOT_PATH
    if not os.path.exists(SHOT_PATH):
        raise HTTPException(404, "Belum Ada Screenshot")
    try:
        with open(SHOT_META_PATH, "r", encoding="utf-8") as f:
            aid = json.load(f).get("account_id")
    except Exception:  # noqa: BLE001
        aid = None
    if not aid or aid not in accessible_ids(user):
        raise HTTPException(404, "Belum Ada Screenshot")
    return FileResponse(SHOT_PATH, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@app.get("/api/proof/{run_id}/{name}")
def proof(run_id: str, name: str, user=Depends(current_user)):
    from .runner import PROOFS_DIR
    if not re.fullmatch(r"[0-9a-f]{8}", run_id) or not re.fullmatch(r"\d+\.jpg", name):
        raise HTTPException(404, "Tidak Ditemukan")
    r = get_run(run_id)
    if not run_accessible_user(user, r):
        raise HTTPException(404, "Tidak Ditemukan")
    path = os.path.join(PROOFS_DIR, run_id, name)
    if not os.path.exists(path):
        raise HTTPException(404, "Bukti Sudah Dihapus")
    return FileResponse(path, media_type="image/jpeg")


def run_accessible_user(user, run):
    return bool(run) and (run.get("account") or {}).get("id") in accessible_ids(user)


HISTORY_MODES = ("send", "check", "test")
HISTORY_STATUS = ("success", "partial", "failed", "expired", "cancelled", "running")


@app.get("/api/history")
def history(account: str = Query("all"), page: int = Query(1, ge=1), page_size: int = Query(20), mode: Optional[str] = Query(None),
            status: Optional[str] = Query(None), user=Depends(current_user)):
    """Riwayat milik pengguna ini (terbaru dulu) dengan paginasi dan filter."""
    if page_size not in (10, 20, 50):
        raise HTTPException(400, "Ukuran Halaman Harus 10, 20, atau 50")
    if mode and mode not in HISTORY_MODES:
        raise HTTPException(400, "Mode Tidak Dikenal")
    if status and status not in HISTORY_STATUS:
        raise HTTPException(400, "Status Tidak Dikenal")
    acc_id = None
    if account != "all":
        acc_id = resolve_account(user, account)["id"]
    items, total = query_runs(user["id"], acc_id, page, page_size, mode, status)
    return {"items": [{**run_view(r), "logs": r.get("logs", [])} for r in items], "total": total, "page": page, "page_size": page_size}


ONBOARDING_STEPS = ("cookie", "contacts", "schedule", "notify", "test")


def _onboarding(acc, user):
    """Daftar langkah awal untuk akun aktif; sembunyi bila semua selesai atau ditutup pengguna."""
    st = stores(acc["id"])
    meta = st.meta.read()
    from .auth import user_notify
    n = user_notify(user)
    done = {
        "cookie": bool(st.cookies.read()) and not meta.get("invalid"),
        "contacts": bool(st.contacts.read()),
        "schedule": any(s["enabled"] for s in acc["schedules"]),
        "notify": bool((n.get("discord_enabled") and n.get("discord_webhook")) or (n.get("telegram_enabled") and n.get("telegram_token") and n.get("telegram_chat_id"))),
        "test": bool(db.q1("SELECT 1 FROM runs WHERE account_id=? AND mode='test' AND status='success' LIMIT 1", (acc["id"],))),
    }
    dismissed = bool(db.q1("SELECT 1 FROM onboarding_dismissed WHERE user_id=? AND account_id=?", (user["id"], acc["id"])))
    count = sum(done.values())
    return {"steps": [{"key": k, "done": done[k]} for k in ONBOARDING_STEPS], "done": count, "total": len(ONBOARDING_STEPS),
            "dismissed": dismissed, "visible": not dismissed and count < len(ONBOARDING_STEPS)}


@app.post("/api/onboarding/dismiss")
def onboarding_dismiss(acc=Depends(acct), user=Depends(current_user)):
    if user.get("synthetic"):
        raise HTTPException(400, "Tidak Tersedia untuk Akses Kunci API")
    db.x("INSERT OR IGNORE INTO onboarding_dismissed(user_id, account_id, dismissed_at) VALUES(?,?,?)",
         (user["id"], acc["id"], datetime.now().isoformat(timespec="seconds")))
    return _onboarding(acc, user)


@app.get("/api/dashboard")
def dashboard(acc=Depends(acct), user=Depends(current_user)):
    """Statistik dashboard lewat query terarah (bukan dari daftar riwayat berhalaman)."""
    today = datetime.now().date()
    d = today.isoformat()
    return {
        "today": d,
        "runs_today": [run_view(r) for r in runs_since(acc["id"], d + "T00:00:00")],
        "send_days": send_days(acc["id"], (today - timedelta(days=400)).isoformat()),
        "week": day_stats(acc["id"], (today - timedelta(days=6)).isoformat()),
        "onboarding": _onboarding(acc, user),
        "needs_check": [{"name": r["name"], "error": r["last_error"]} for r in _contact_rows(acc) if r["today"] == "failed"],
    }


@app.delete("/api/history")
def clear_history(user=Depends(current_user)):
    delete_runs(owner_id=user["id"])
    return {"ok": True}


# ---------------------------------------------------------------- frontend
class VersionedStatic(StaticFiles):
    """File statis: immutable bila diminta dengan ?v=, selain itu selalu revalidasi (ETag)."""

    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        if resp.status_code in (200, 304):
            if b"v=" in scope.get("query_string", b""):
                resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            else:
                resp.headers["Cache-Control"] = "no-cache"
        return resp


def _asset_version():
    h = hashlib.sha1()
    for name in ("app.js", "style.css", "index.html"):
        try:
            with open(os.path.join(STATIC, name), "rb") as f:
                h.update(f.read())
        except OSError:
            pass
    return h.hexdigest()[:10]


ASSET_VER = _asset_version()
app.mount("/static", VersionedStatic(directory=STATIC), name="static")

HTML_HEADERS = {"Cache-Control": "private, no-cache", "Vary": "Cookie"}  # di belakang CDN: HTML tidak boleh disimpan cache bersama


def _page(name, response=None):
    with open(os.path.join(STATIC, name), "r", encoding="utf-8") as f:
        html = f.read()
    for asset in ("style.css", "app.js", "landing.css", "landing.js"):
        html = html.replace(f"/static/{asset}", f"/static/{asset}?v={ASSET_VER}")
    if name == "index.html" and config.LANDING_ENABLED:
        html = html.replace('<html lang="id">', '<html lang="id" data-landing="1">', 1)
    url = config.LANDING_DOCS_URL
    if not re.match(r"^https?://", url, re.I):
        url = ""
    html = html.replace("__DOCS_URL__", url.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;"))
    out = Response(html, media_type="text/html; charset=utf-8", headers=HTML_HEADERS)
    if response is not None:  # teruskan cookie hasil upgrade sesi lama
        for k, v in response.raw_headers:
            if k.lower() == b"set-cookie":
                out.raw_headers.append((k, v))
    return out


@app.get("/", include_in_schema=False)
def index(request: Request, response: Response):
    if not config.LANDING_ENABLED:
        return _page("index.html")
    if users_count() == 0:
        return RedirectResponse("/login", status_code=302, headers=HTML_HEADERS)
    token = session_token(request)
    if token and user_from_token(token):
        if not request.cookies.get(COOKIE) and request.cookies.get(LEGACY_COOKIE):
            set_cookie(request, response, token)  # upgrade sesi lama ke bara_session
            response.delete_cookie(LEGACY_COOKIE, path="/")
        return _page("index.html", response)
    return _page("landing.html")


@app.get("/login", include_in_schema=False)
def login_page(request: Request, response: Response):
    token = session_token(request)
    if token and user_from_token(token):
        return RedirectResponse("/", status_code=302, headers=HTML_HEADERS)
    return _page("index.html")
