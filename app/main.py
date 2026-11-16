import json
import os
import re
from datetime import datetime
import secrets
import uuid
import threading
from typing import List, Optional
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config
from .auth import (
    accessible_ids,
    can_access,
    current_user,
    is_admin,
    owner_for_new,
    public_user,
    require_admin,
    router as auth_router,
    visible_accounts,
)
from .cookies import parse_cookies, summary
from .login import login_session
from .notify import DISCORD_RE, send_discord, send_telegram
from .runner import Busy, runner
from .store import (
    DEFAULT_SETTINGS,
    create_account,
    delete_account,
    get_account,
    get_settings,
    history_store,
    list_accounts,
    rename_contact,
    save_account,
    settings_store,
    stores,
)
from .auth import get_user

if not config.API_KEY:
    raise SystemExit("API_KEY belum diatur. Isi API_KEY pada file .env")

app = FastAPI(title="TikTok Streak Panel", docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(auth_router)
STATIC = os.path.join(os.path.dirname(__file__), "static")


auth = current_user


def resolve_account(user, account_id):
    """Akun milik/diizinkan untuk pemanggil; 404 bila tidak ada atau bukan haknya."""
    accs = visible_accounts(user)
    if not account_id:
        if not accs:
            raise HTTPException(404, "Akun tidak ditemukan")
        return accs[0]
    found = next((a for a in accs if a["id"] == account_id), None)
    if not found:
        raise HTTPException(404, "Akun tidak ditemukan")
    return found


def acct(account: Optional[str] = Query(None), user=Depends(current_user)):
    """Akun yang dipilih lewat ?account=ID (default: akun pertama yang boleh diakses)."""
    return resolve_account(user, account)


@app.on_event("startup")
def _startup():
    threading.Thread(target=runner.scheduler_loop, daemon=True).start()


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
    notify_all_accounts: Optional[bool] = None
    keepalive_enabled: Optional[bool] = None
    keepalive_hours: Optional[int] = None
    page_load_wait: Optional[int] = None
    element_wait: Optional[int] = None
    send_delay: Optional[int] = None


class AccountIn(BaseModel):
    name: Optional[str] = None
    owner_id: Optional[str] = None
    schedules: Optional[List[ScheduleIn]] = None


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


def public_settings():
    s = get_settings()
    token = s.pop("telegram_token")
    s["telegram_token_set"] = bool(token)
    s["discord_webhook_set"] = bool(s.pop("discord_webhook"))
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
def health():
    return {"status": "ok"}


def account_view(acc, user=None):
    st = stores(acc["id"])
    extra = {}
    if user is not None and is_admin(user):
        owner = get_user(acc.get("owner_id")) if acc.get("owner_id") else None
        extra = {"owner_id": acc.get("owner_id"), "owner_name": owner["username"] if owner else None}
    return {
        **extra,
        "id": acc["id"],
        "name": acc["name"],
        "contacts": len(st.contacts.read()),
        "cookies": cookie_view(acc["id"]),
        "schedules": acc["schedules"],
        "next_run": runner.next_run_at(acc["id"]),
        "next": runner.next_schedule(acc["id"]),
    }


def _login_visible(user):
    return login_session.active and (is_admin(user) or login_session.owner_id == user["id"])


@app.get("/api/status")
def status(user=Depends(current_user)):
    ids = accessible_ids(user)
    hist = [r for r in history_store.read() if is_admin(user) or (r.get("account") or {}).get("id") in ids]
    cur = runner.current
    running = bool(cur and cur["status"] == "running")
    cur_ok = bool(cur) and (is_admin(user) or cur["account"]["id"] in ids)
    return {
        "running": running,
        "foreign_busy": running and not cur_ok,
        "current": run_view(cur) if cur_ok else None,
        "last_run": run_view(hist[0]) if hist else None,
        "accounts": [account_view(a, user) for a in visible_accounts(user)],
        "login": login_session.account_id if _login_visible(user) else None,
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
            raise HTTPException(400, "Timezone tidak dikenal")
    if "message" in data and not data["message"].strip():
        raise HTTPException(400, "Pesan tidak boleh kosong")
    if "keepalive_hours" in data and not 1 <= data["keepalive_hours"] <= 72:
        raise HTTPException(400, "keepalive_hours harus 1-72")
    for k in ("page_load_wait", "element_wait", "send_delay"):
        if k in data and not 0 <= data[k] <= 60:
            raise HTTPException(400, f"{k} harus 0-60 detik")
    for k in ("telegram_token", "discord_webhook"):
        if data.get(k) == "":
            data.pop(k)
    if "discord_webhook" in data and data["discord_webhook"] != "-" and not DISCORD_RE.match(data["discord_webhook"]):
        raise HTTPException(400, "URL webhook Discord tidak valid")
    if data.get("discord_webhook") == "-":  # hapus webhook
        data["discord_webhook"] = ""
    merged = {**get_settings(), **data}
    settings_store.write({k: merged[k] for k in DEFAULT_SETTINGS})
    return public_settings()


@app.post("/api/telegram/test", dependencies=[Depends(require_admin)])
def telegram_test():
    ok, err = send_telegram(get_settings(), "✅ Tes notifikasi dari TikTok Streak Panel")
    if not ok:
        raise HTTPException(400, err)
    return {"ok": True}


@app.post("/api/discord/test", dependencies=[Depends(require_admin)])
def discord_test():
    ok, err = send_discord(get_settings(), "✅ Tes notifikasi dari TikTok Streak Panel")
    if not ok:
        raise HTTPException(400, err)
    return {"ok": True}


def clean_schedules(items):
    if len(items) > 8:
        raise HTTPException(400, "Maksimal 8 jadwal per akun")
    clean, seen = [], set()
    for x in items:
        x = x.model_dump()
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", x["time"]):
            raise HTTPException(400, "Format jam harus HH:MM")
        if len(x["message"]) > 500:
            raise HTTPException(400, "Pesan jadwal maksimal 500 karakter")
        sid = x["id"] if x.get("id") and x["id"] not in seen else uuid.uuid4().hex[:6]
        seen.add(sid)
        contacts = x.get("contacts")
        if contacts is not None:
            contacts = list(dict.fromkeys(c.strip() for c in contacts if c.strip()))[:200]
            if not contacts:
                raise HTTPException(400, f"Jadwal {x['time']}: pilih minimal satu kontak atau pilih semua kontak")
        clean.append({"id": sid, "enabled": bool(x["enabled"]), "time": x["time"],
                      "message": x["message"].strip(), "contacts": contacts})
    return clean


def clean_name(name, owner_id, exclude_id=None):
    name = (name or "").strip()
    if not 1 <= len(name) <= 40:
        raise HTTPException(400, "Nama akun 1-40 karakter")
    taken = {a["name"].lower() for a in list_accounts() if a.get("owner_id") == owner_id and a["id"] != exclude_id}
    if name.lower() in taken:
        raise HTTPException(400, "Nama akun sudah dipakai")
    return name


@app.get("/api/accounts")
def accounts(user=Depends(current_user)):
    return {"accounts": [account_view(a, user) for a in visible_accounts(user)]}


@app.post("/api/accounts")
def add_account(body: AccountIn, user=Depends(current_user)):
    owner = owner_for_new(user)
    if len(list_accounts()) >= 10:
        raise HTTPException(400, "Maksimal 10 akun")
    if user["role"] == "user" and sum(1 for a in list_accounts() if a.get("owner_id") == owner) >= 5:
        raise HTTPException(400, "Maksimal 5 akun per pengguna")
    acc = create_account(clean_name(body.name, owner), owner)
    return account_view(acc, user)


@app.put("/api/accounts/{aid}")
def update_account(aid: str, body: AccountIn, user=Depends(current_user)):
    acc = resolve_account(user, aid)
    if body.owner_id is not None and body.owner_id != acc.get("owner_id"):
        if not is_admin(user):
            raise HTTPException(403, "Hanya admin yang boleh memindahkan pemilik akun")
        new_owner = get_user(body.owner_id)
        if not new_owner or new_owner.get("disabled"):
            raise HTTPException(400, "Pemilik baru tidak valid")
        old = acc.get("owner_id")
        acc["owner_id"] = new_owner["id"]
        save_account(acc)
        if old:
            from .auth import ensure_default_account
            old_user = get_user(old)
            if old_user and old_user["role"] == "user" and not old_user.get("disabled"):
                ensure_default_account(old)
    if body.name is not None and body.name.strip() != acc["name"]:
        acc["name"] = clean_name(body.name, acc.get("owner_id"), aid)
    if body.schedules is not None:
        acc["schedules"] = clean_schedules(body.schedules)
    save_account(acc)
    return account_view(acc, user)


@app.delete("/api/accounts/{aid}")
def remove_account(aid: str, user=Depends(current_user)):
    acc = resolve_account(user, aid)
    mine = [a for a in list_accounts() if a.get("owner_id") == acc.get("owner_id")]
    if len(list_accounts()) <= 1 or (acc.get("owner_id") and len(mine) <= 1):
        raise HTTPException(400, "Minimal harus ada satu akun")
    if runner.current and runner.current["status"] == "running" and runner.current["account"]["id"] == aid:
        raise HTTPException(409, "Akun sedang dipakai proses yang berjalan")
    if login_session.active and login_session.account_id == aid:
        login_session.stop()
    delete_account(aid)
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
        raise HTTPException(400, "Tidak ada kontak baru (kosong atau sudah ada)")
    contacts_store.write(current)
    return {"contacts": current, "added": added}


@app.put("/api/contacts/rename", dependencies=[Depends(current_user)])
def rename_contact_api(body: RenameIn, acc=Depends(acct)):
    old, new = body.old.strip(), body.new.strip()
    current = stores(acc["id"]).contacts.read()
    if old.lower() not in {c.lower() for c in current}:
        raise HTTPException(404, "Kontak tidak ditemukan")
    if not new or len(new) > 100:
        raise HTTPException(400, "Nama baru 1-100 karakter")
    if new.lower() != old.lower() and new.lower() in {c.lower() for c in current}:
        raise HTTPException(409, "Nama baru sudah ada di daftar kontak")
    rename_contact(acc["id"], old, new)
    return {"contacts": stores(acc["id"]).contacts.read()}


@app.delete("/api/contacts", dependencies=[Depends(current_user)])
def delete_contact(name: str = Query(...), acc=Depends(acct)):
    contacts_store = stores(acc["id"]).contacts
    current = contacts_store.read()
    new = [c for c in current if c.lower() != name.lower()]
    if len(new) == len(current):
        raise HTTPException(404, "Kontak tidak ditemukan")
    contacts_store.write(new)
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


def _login_call(fn, *a):
    try:
        return fn(*a)
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Browser error: {e}")


def _login_guard(user):
    """Sesi login remote hanya boleh dipakai pemiliknya atau admin."""
    if login_session.active and not (is_admin(user) or login_session.owner_id == user["id"]):
        raise HTTPException(403, "Sesi login sedang dipakai pengguna lain")


@app.post("/api/login/start")
def login_start(acc=Depends(acct), user=Depends(current_user)):
    if runner.current and runner.current["status"] == "running":
        raise HTTPException(409, "Tunggu proses yang sedang berjalan selesai")
    _login_guard(user)
    was_active = login_session.active
    _login_call(login_session.start, acc["id"])
    if not was_active:
        login_session.owner_id = user["id"]
    return {"ok": True}


@app.get("/api/login/status")
def login_status(user=Depends(current_user)):
    _login_guard(user)
    return _login_call(login_session.status)


@app.get("/api/login/frame")
def login_frame(user=Depends(current_user)):
    _login_guard(user)
    return Response(_login_call(login_session.frame), media_type="image/jpeg",
                    headers={"Cache-Control": "no-store"})


@app.post("/api/login/input")
def login_input(body: LoginInput, user=Depends(current_user)):
    _login_guard(user)
    _login_call(login_session.input, body.model_dump())
    return {"ok": True}


@app.post("/api/login/save")
def login_save(user=Depends(current_user)):
    _login_guard(user)
    aid = login_session.account_id
    n = _login_call(login_session.save)
    login_session.stop()
    reset_cookie_meta(aid)
    return {"saved": n, **cookie_view(aid)}


@app.post("/api/login/stop")
def login_stop(user=Depends(current_user)):
    _login_guard(user)
    login_session.stop()
    return {"ok": True}


@app.post("/api/run")
def run(body: RunIn, user=Depends(current_user)):
    acc = resolve_account(user, body.account)
    if body.mode not in ("send", "test", "check"):
        raise HTTPException(400, "mode harus send, test, atau check")
    if login_session.active:
        raise HTTPException(409, "Tutup sesi login di tab Cookie dulu")
    try:
        r = runner.start(acc["id"], body.mode, body.message.strip() if body.message else None, by=user["username"])
    except Busy:
        raise HTTPException(409, "Masih ada proses yang berjalan")
    return run_view(r)


@app.post("/api/run/stop")
def stop(user=Depends(current_user)):
    cur = runner.current
    if cur and cur["status"] == "running" and not can_access(user, get_account(cur["account"]["id"]) or {}):
        raise HTTPException(403, "Proses ini bukan milik Anda")
    runner.stop()
    return {"ok": True}


@app.get("/api/run/current")
def current(since: int = 0, user=Depends(current_user)):
    cur = runner.current
    running = bool(cur and cur["status"] == "running")
    if not cur or not (is_admin(user) or cur["account"]["id"] in accessible_ids(user)):
        return {"run": None, "logs": [], "next": 0, "running": running}
    logs = cur["logs"]
    return {"run": run_view(cur), "logs": logs[since:], "next": len(logs), "running": running}


@app.get("/api/run/screenshot")
def run_screenshot(user=Depends(current_user)):
    from .bot import SHOT_META_PATH, SHOT_PATH
    if not os.path.exists(SHOT_PATH):
        raise HTTPException(404, "Belum ada screenshot")
    if not is_admin(user):
        try:
            with open(SHOT_META_PATH, "r", encoding="utf-8") as f:
                aid = json.load(f).get("account_id")
        except Exception:  # noqa: BLE001
            aid = None
        if not aid or aid not in accessible_ids(user):
            raise HTTPException(404, "Belum ada screenshot")
    return FileResponse(SHOT_PATH, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@app.get("/api/proof/{run_id}/{name}")
def proof(run_id: str, name: str, user=Depends(current_user)):
    from .runner import PROOFS_DIR
    if not re.fullmatch(r"[0-9a-f]{8}", run_id) or not re.fullmatch(r"\d+\.jpg", name):
        raise HTTPException(404, "Tidak ditemukan")
    if not is_admin(user):
        r = next((x for x in history_store.read() if x.get("id") == run_id), None)
        if not run_accessible_user(user, r):
            raise HTTPException(404, "Tidak ditemukan")
    path = os.path.join(PROOFS_DIR, run_id, name)
    if not os.path.exists(path):
        raise HTTPException(404, "Bukti sudah dihapus")
    return FileResponse(path, media_type="image/jpeg")


def run_accessible_user(user, run):
    return bool(run) and (run.get("account") or {}).get("id") in accessible_ids(user)


@app.get("/api/history")
def history(user=Depends(current_user)):
    ids = accessible_ids(user)
    return {"runs": [{**run_view(r), "logs": r.get("logs", [])} for r in history_store.read()
                     if is_admin(user) or (r.get("account") or {}).get("id") in ids]}


@app.delete("/api/history")
def clear_history(user=Depends(current_user)):
    if is_admin(user):
        history_store.write([])
    else:
        ids = accessible_ids(user)
        history_store.write([r for r in history_store.read() if (r.get("account") or {}).get("id") not in ids])
    return {"ok": True}


# ---------------------------------------------------------------- frontend
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(STATIC, "index.html"))
