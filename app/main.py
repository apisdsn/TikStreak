import os
import re
import secrets
import threading
from typing import Optional
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
    contacts_store,
    cookies_store,
    get_settings,
    history_store,
    settings_store,
)

if not config.API_KEY:
    raise SystemExit("API_KEY belum diatur. Isi API_KEY pada file .env")

app = FastAPI(title="TikTok Streak Panel", docs_url=None, redoc_url=None, openapi_url=None)
STATIC = os.path.join(os.path.dirname(__file__), "static")


def auth(x_api_key: Optional[str] = Header(None)):
    if not x_api_key or not secrets.compare_digest(x_api_key, config.API_KEY):
        raise HTTPException(401, "Access key salah atau tidak ada")


@app.on_event("startup")
def _startup():
    threading.Thread(target=runner.scheduler_loop, daemon=True).start()


# ---------------------------------------------------------------- schemas
class SettingsIn(BaseModel):
    message: Optional[str] = None
    schedule_enabled: Optional[bool] = None
    schedule_time: Optional[str] = None
    timezone: Optional[str] = None
    telegram_enabled: Optional[bool] = None
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    discord_enabled: Optional[bool] = None
    discord_webhook: Optional[str] = None
    page_load_wait: Optional[int] = None
    element_wait: Optional[int] = None
    send_delay: Optional[int] = None


class ContactsIn(BaseModel):
    names: str


class CookiesIn(BaseModel):
    raw: str


class RunIn(BaseModel):
    mode: str = "send"
    message: Optional[str] = None


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
    keys = ("id", "mode", "trigger", "status", "started_at", "finished_at", "sent", "total", "error")
    out = {k: run.get(k) for k in keys}
    out["results"] = run.get("results", [])
    if with_logs:
        out["logs"] = run.get("logs", [])
    return out


# -------------------------------------------------------------------- API
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/status", dependencies=[Depends(auth)])
def status():
    hist = history_store.read()
    cur = runner.current
    return {
        "running": bool(cur and cur["status"] == "running"),
        "current": run_view(cur),
        "last_run": run_view(hist[0]) if hist else None,
        "next_run": runner.next_run_at(),
        "contacts": len(contacts_store.read()),
        "cookies": summary(cookies_store.read()),
        "schedule_enabled": get_settings()["schedule_enabled"],
    }


@app.get("/api/settings", dependencies=[Depends(auth)])
def read_settings():
    return public_settings()


@app.put("/api/settings", dependencies=[Depends(auth)])
def write_settings(body: SettingsIn):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if "schedule_time" in data and not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", data["schedule_time"]):
        raise HTTPException(400, "Format jam harus HH:MM")
    if data.get("timezone"):
        try:
            ZoneInfo(data["timezone"])
        except Exception:
            raise HTTPException(400, "Timezone tidak dikenal")
    if "message" in data and not data["message"].strip():
        raise HTTPException(400, "Pesan tidak boleh kosong")
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


@app.get("/api/contacts", dependencies=[Depends(auth)])
def list_contacts():
    return {"contacts": contacts_store.read()}


@app.post("/api/contacts", dependencies=[Depends(auth)])
def add_contacts(body: ContactsIn):
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
def delete_contact(name: str = Query(...)):
    current = contacts_store.read()
    new = [c for c in current if c.lower() != name.lower()]
    if len(new) == len(current):
        raise HTTPException(404, "Kontak tidak ditemukan")
    contacts_store.write(new)
    return {"contacts": new}


@app.get("/api/cookies", dependencies=[Depends(auth)])
def cookie_status():
    return summary(cookies_store.read())


@app.put("/api/cookies", dependencies=[Depends(auth)])
def set_cookies(body: CookiesIn):
    try:
        cookies = parse_cookies(body.raw)
    except ValueError as e:
        raise HTTPException(400, str(e))
    cookies_store.write(cookies)
    return summary(cookies)


@app.delete("/api/cookies", dependencies=[Depends(auth)])
def clear_cookies():
    cookies_store.delete()
    return summary([])


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
def login_start():
    if runner.current and runner.current["status"] == "running":
        raise HTTPException(409, "Tunggu proses yang sedang berjalan selesai")
    _login_call(login_session.start)
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
    n = _login_call(login_session.save)
    login_session.stop()
    return {"saved": n, **summary(cookies_store.read())}


@app.post("/api/login/stop", dependencies=[Depends(auth)])
def login_stop():
    login_session.stop()
    return {"ok": True}


@app.post("/api/run", dependencies=[Depends(auth)])
def run(body: RunIn):
    if body.mode not in ("send", "test"):
        raise HTTPException(400, "mode harus send atau test")
    if login_session.active:
        raise HTTPException(409, "Tutup sesi login di tab Cookie dulu")
    try:
        r = runner.start(body.mode, body.message.strip() if body.message else None)
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
