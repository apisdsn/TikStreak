import os
import re
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
    save_account,
    settings_store,
    stores,
)

if not config.API_KEY:
    raise SystemExit("API_KEY belum diatur. Isi API_KEY pada file .env")

app = FastAPI(title="TikTok Streak Panel", docs_url=None, redoc_url=None, openapi_url=None)
STATIC = os.path.join(os.path.dirname(__file__), "static")


def auth(x_api_key: Optional[str] = Header(None)):
    if not x_api_key or not secrets.compare_digest(x_api_key, config.API_KEY):
        raise HTTPException(401, "Access key salah atau tidak ada")


def acct(account: Optional[str] = Query(None)):
    """Akun yang dipilih lewat ?account=ID (default: akun pertama)."""
    accs = list_accounts()
    if not account:
        return accs[0]
    found = next((a for a in accs if a["id"] == account), None)
    if not found:
        raise HTTPException(404, "Akun tidak ditemukan")
    return found


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
    keepalive_enabled: Optional[bool] = None
    keepalive_hours: Optional[int] = None
    page_load_wait: Optional[int] = None
    element_wait: Optional[int] = None
    send_delay: Optional[int] = None


class AccountIn(BaseModel):
    name: Optional[str] = None
    schedules: Optional[List[ScheduleIn]] = None


class ContactsIn(BaseModel):
    names: str


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
    keys = ("id", "account", "mode", "trigger", "label", "status", "started_at", "finished_at", "sent", "total", "error")
    out = {k: run.get(k) for k in keys}
    out["results"] = run.get("results", [])
    if with_logs:
        out["logs"] = run.get("logs", [])
    return out


# -------------------------------------------------------------------- API
@app.get("/api/health")
def health():
    return {"status": "ok"}


def account_view(acc):
    st = stores(acc["id"])
    return {
        "id": acc["id"],
        "name": acc["name"],
        "contacts": len(st.contacts.read()),
        "cookies": cookie_view(acc["id"]),
        "schedules": acc["schedules"],
        "next_run": runner.next_run_at(acc["id"]),
    }


@app.get("/api/status", dependencies=[Depends(auth)])
def status():
    hist = history_store.read()
    cur = runner.current
    return {
        "running": bool(cur and cur["status"] == "running"),
        "current": run_view(cur),
        "last_run": run_view(hist[0]) if hist else None,
        "accounts": [account_view(a) for a in list_accounts()],
        "login": login_session.account_id,
    }


@app.get("/api/settings", dependencies=[Depends(auth)])
def read_settings():
    return public_settings()


@app.put("/api/settings", dependencies=[Depends(auth)])
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


@app.post("/api/telegram/test", dependencies=[Depends(auth)])
def telegram_test():
    ok, err = send_telegram(get_settings(), "✅ Tes notifikasi dari TikTok Streak Panel")
    if not ok:
        raise HTTPException(400, err)
    return {"ok": True}


@app.post("/api/discord/test", dependencies=[Depends(auth)])
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


def clean_name(name):
    name = (name or "").strip()
    if not 1 <= len(name) <= 40:
        raise HTTPException(400, "Nama akun 1-40 karakter")
    if name.lower() in {a["name"].lower() for a in list_accounts()}:
        raise HTTPException(400, "Nama akun sudah dipakai")
    return name


@app.get("/api/accounts", dependencies=[Depends(auth)])
def accounts():
    return {"accounts": [account_view(a) for a in list_accounts()]}


@app.post("/api/accounts", dependencies=[Depends(auth)])
def add_account(body: AccountIn):
    if len(list_accounts()) >= 10:
        raise HTTPException(400, "Maksimal 10 akun")
    acc = create_account(clean_name(body.name))
    return account_view(acc)


@app.put("/api/accounts/{aid}", dependencies=[Depends(auth)])
def update_account(aid: str, body: AccountIn):
    acc = get_account(aid)
    if not acc:
        raise HTTPException(404, "Akun tidak ditemukan")
    if body.name is not None and body.name.strip() != acc["name"]:
        acc["name"] = clean_name(body.name)
    if body.schedules is not None:
        acc["schedules"] = clean_schedules(body.schedules)
    save_account(acc)
    return account_view(acc)


@app.delete("/api/accounts/{aid}", dependencies=[Depends(auth)])
def remove_account(aid: str):
    if not get_account(aid):
        raise HTTPException(404, "Akun tidak ditemukan")
    if len(list_accounts()) <= 1:
        raise HTTPException(400, "Minimal harus ada satu akun")
    if runner.current and runner.current["status"] == "running" and runner.current["account"]["id"] == aid:
        raise HTTPException(409, "Akun sedang dipakai proses yang berjalan")
    if login_session.active and login_session.account_id == aid:
        login_session.stop()
    delete_account(aid)
    return {"ok": True}


@app.get("/api/contacts", dependencies=[Depends(auth)])
def list_contacts(acc=Depends(acct)):
    return {"contacts": stores(acc["id"]).contacts.read()}


@app.post("/api/contacts", dependencies=[Depends(auth)])
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


@app.delete("/api/contacts", dependencies=[Depends(auth)])
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


@app.get("/api/cookies", dependencies=[Depends(auth)])
def cookie_status(acc=Depends(acct)):
    return cookie_view(acc["id"])


@app.put("/api/cookies", dependencies=[Depends(auth)])
def set_cookies(body: CookiesIn, acc=Depends(acct)):
    try:
        cookies = parse_cookies(body.raw)
    except ValueError as e:
        raise HTTPException(400, str(e))
    stores(acc["id"]).cookies.write(cookies)
    reset_cookie_meta(acc["id"])
    return cookie_view(acc["id"])


@app.delete("/api/cookies", dependencies=[Depends(auth)])
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


@app.post("/api/login/start", dependencies=[Depends(auth)])
def login_start(acc=Depends(acct)):
    if runner.current and runner.current["status"] == "running":
        raise HTTPException(409, "Tunggu proses yang sedang berjalan selesai")
    _login_call(login_session.start, acc["id"])
    return {"ok": True}


@app.get("/api/login/status", dependencies=[Depends(auth)])
def login_status():
    return _login_call(login_session.status)


@app.get("/api/login/frame", dependencies=[Depends(auth)])
def login_frame():
    return Response(_login_call(login_session.frame), media_type="image/jpeg",
                    headers={"Cache-Control": "no-store"})


@app.post("/api/login/input", dependencies=[Depends(auth)])
def login_input(body: LoginInput):
    _login_call(login_session.input, body.model_dump())
    return {"ok": True}


@app.post("/api/login/save", dependencies=[Depends(auth)])
def login_save():
    aid = login_session.account_id
    n = _login_call(login_session.save)
    login_session.stop()
    reset_cookie_meta(aid)
    return {"saved": n, **cookie_view(aid)}


@app.post("/api/login/stop", dependencies=[Depends(auth)])
def login_stop():
    login_session.stop()
    return {"ok": True}


@app.post("/api/run", dependencies=[Depends(auth)])
def run(body: RunIn):
    acc = acct(body.account)
    if body.mode not in ("send", "test", "check"):
        raise HTTPException(400, "mode harus send, test, atau check")
    if login_session.active:
        raise HTTPException(409, "Tutup sesi login di tab Cookie dulu")
    try:
        r = runner.start(acc["id"], body.mode, body.message.strip() if body.message else None)
    except Busy:
        raise HTTPException(409, "Masih ada proses yang berjalan")
    return run_view(r)


@app.post("/api/run/stop", dependencies=[Depends(auth)])
def stop():
    runner.stop()
    return {"ok": True}


@app.get("/api/run/current", dependencies=[Depends(auth)])
def current(since: int = 0):
    cur = runner.current
    if not cur:
        return {"run": None, "logs": [], "next": 0}
    logs = cur["logs"]
    return {"run": run_view(cur), "logs": logs[since:], "next": len(logs)}


@app.get("/api/run/screenshot", dependencies=[Depends(auth)])
def run_screenshot():
    from .bot import SHOT_PATH
    if not os.path.exists(SHOT_PATH):
        raise HTTPException(404, "Belum ada screenshot")
    return FileResponse(SHOT_PATH, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@app.get("/api/proof/{run_id}/{name}", dependencies=[Depends(auth)])
def proof(run_id: str, name: str):
    from .runner import PROOFS_DIR
    if not re.fullmatch(r"[0-9a-f]{8}", run_id) or not re.fullmatch(r"\d+\.jpg", name):
        raise HTTPException(404, "Tidak ditemukan")
    path = os.path.join(PROOFS_DIR, run_id, name)
    if not os.path.exists(path):
        raise HTTPException(404, "Bukti sudah dihapus")
    return FileResponse(path, media_type="image/jpeg")


@app.get("/api/history", dependencies=[Depends(auth)])
def history():
    return {"runs": [{**run_view(r), "logs": r.get("logs", [])} for r in history_store.read()]}


@app.delete("/api/history", dependencies=[Depends(auth)])
def clear_history():
    history_store.write([])
    return {"ok": True}


# ---------------------------------------------------------------- frontend
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(STATIC, "index.html"))
