"""Pengguna, sesi cookie, throttling login, dan otorisasi akses akun."""
import hashlib
import hmac
import os
import re
import secrets
import threading
import time
import uuid
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel

from . import config, db
from .notify import DISCORD_RE, send_discord, send_telegram
from .store import (
    create_account,
    list_accounts,
    save_account,
    session_del,
    session_get,
    session_put,
    sessions_del_user,
    user_by_name,
    user_delete,
    user_get,
    user_save,
    users_all,
    users_count,
)

ITERATIONS = 600_000
SESSION_TTL = 7 * 24 * 3600
COOKIE = "bara_session"
LEGACY_COOKIE = "sp_session"  # TODO: hapus setelah semua sesi lama berpindah ke bara_session
CSRF_HEADER = "bara"
LEGACY_CSRF_HEADER = "streak-panel"  # TODO: hapus setelah semua browser memakai JS terbaru
MAX_FAILS = 5
FAIL_WINDOW = 15 * 60
LOCK_TIME = 15 * 60
USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,32}$")

_lock = threading.RLock()

router = APIRouter()


# ------------------------------------------------------------------ password
def hash_password(password, salt=None, iterations=ITERATIONS):
    salt = salt or secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return {"pw_hash": h.hex(), "salt": salt.hex(), "iterations": iterations}


def verify_password(user, password):
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(user["salt"]), user["iterations"])
    return hmac.compare_digest(h.hex(), user["pw_hash"])


_dummy = None


def _dummy_user():
    global _dummy
    if _dummy is None:
        _dummy = {**hash_password("dummy-password"), "role": "user"}
    return _dummy


def check_password_rules(password):
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        raise HTTPException(400, "Kata Sandi Harus 8-128 Karakter")


def clean_username(name):
    name = (name or "").strip().lower()
    if not USERNAME_RE.match(name):
        raise HTTPException(400, "Nama Pengguna 3-32 Karakter: Huruf Kecil, Angka, Titik, Garis Bawah, atau Strip")
    return name


# --------------------------------------------------------------------- users
def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def list_users():
    return users_all()


def get_user(uid):
    return user_get(uid)


def find_by_username(name):
    return user_by_name(name)


def active_admins():
    return [u for u in list_users() if u["role"] == "admin" and not u.get("disabled")]


def public_user(u):
    return {"id": u["id"], "username": u["username"], "role": u["role"]}


def make_user(username, password, role):
    return {"id": uuid.uuid4().hex[:8], "username": username, **hash_password(password), "role": role,
            "disabled": False, "created_at": now_iso(), "pw_changed_at": now_iso()}


def _stop_login_of(uid):
    from .login import login_mgr
    login_mgr.stop_owner(uid)


def ensure_default_account(uid):
    """Setiap pengguna aktif minimal punya satu akun TikTok."""
    if not any(a.get("owner_id") == uid for a in list_accounts()):
        names = {a["name"].lower() for a in list_accounts() if a.get("owner_id") == uid}
        create_account("Utama" if "utama" not in names else "Akun 1", uid)


# ------------------------------------------------------------------ sessions
def _hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(user_id):
    token = secrets.token_urlsafe(32)
    session_put(_hash_token(token), user_id, time.time(), time.time() + SESSION_TTL)
    return token


def drop_session(token):
    session_del(_hash_token(token))


def invalidate_user_sessions(user_id, keep_hash=None):
    sessions_del_user(user_id, keep_hash)


def user_from_token(token):
    if not token:
        return None
    h = _hash_token(token)
    s = session_get(h)
    if not s or s["expires"] <= time.time():
        return None
    u = get_user(s["user_id"])
    if not u or u.get("disabled"):
        return None
    return {**u, "session": h}


def set_cookie(request, response, token):
    https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "").split(",")[0].strip() == "https"
    response.set_cookie(COOKIE, token, max_age=SESSION_TTL, httponly=True, samesite="strict", secure=https, path="/")


# ------------------------------------------------------------------ throttle
_fails = {}
_locked = {}
_tlock = threading.Lock()


def _keys(request, username):
    ip = request.client.host if request.client else "?"
    return [f"ip:{ip}", f"user:{(username or '').strip().lower()}"]


def throttle_check(keys):
    now = time.time()
    with _tlock:
        for k in keys:
            if _locked.get(k, 0) > now:
                raise HTTPException(429, "Terlalu Banyak Percobaan Gagal. Coba Lagi Beberapa Menit Lagi.")


def throttle_fail(keys):
    now = time.time()
    with _tlock:
        for k in keys:
            fl = [t for t in _fails.get(k, []) if now - t < FAIL_WINDOW] + [now]
            _fails[k] = fl
            if len(fl) >= MAX_FAILS:
                _locked[k] = now + LOCK_TIME
                _fails[k] = []
        for k in [k for k, v in _locked.items() if v <= now]:
            del _locked[k]


def throttle_ok(keys):
    with _tlock:
        for k in keys:
            _fails.pop(k, None)


# ---------------------------------------------------------------------- CSRF
def csrf_ok(request):
    if request.headers.get("x-requested-with") not in (CSRF_HEADER, LEGACY_CSRF_HEADER):
        return False
    origin = request.headers.get("origin")
    if origin:
        host = (config.TRUST_PROXY and request.headers.get("x-forwarded-host")) or request.headers.get("host", "")
        if urlparse(origin).netloc != host and urlparse(origin).netloc != request.headers.get("host", ""):
            return False
    return True


def require_csrf(request):
    if not csrf_ok(request):
        raise HTTPException(403, "Permintaan Ditolak (CSRF)")


# ---------------------------------------------------------------- dependency
API_USER = {"id": "apikey", "username": "api", "role": "admin", "synthetic": True, "session": None}


def api_key_user():
    """Akses X-API-Key bertindak sebagai admin aktif tertua (hanya melihat akun miliknya)."""
    admins = active_admins()
    return {**admins[0], "synthetic": True, "session": None} if admins else API_USER


def session_token(request):
    """Token sesi dari cookie baru, atau cookie lama (sp_session) saat masa transisi."""
    return request.cookies.get(COOKIE) or request.cookies.get(LEGACY_COOKIE)


def current_user(request: Request, response: Response, x_api_key: Optional[str] = Header(None)):
    if x_api_key:
        if config.API_KEY and secrets.compare_digest(x_api_key, config.API_KEY):
            return api_key_user()
        raise HTTPException(401, "Kunci API Salah atau Tidak Ada")
    token = session_token(request)
    user = user_from_token(token)
    if not user:
        raise HTTPException(401, "Belum Masuk")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        require_csrf(request)
    if not request.cookies.get(COOKIE) and request.cookies.get(LEGACY_COOKIE):
        # pindahkan sesi lama ke nama cookie baru tanpa memaksa login ulang
        set_cookie(request, response, token)
        response.delete_cookie(LEGACY_COOKIE, path="/")
    return user


def require_admin(user=Depends(current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Hanya Admin yang Boleh Melakukan Ini")
    return user


# ------------------------------------------------------------------- akses
def is_admin(user):
    return user["role"] == "admin"


# Peran admin hanya untuk mengelola pengguna dan pengaturan global: akun TikTok hanya milik pemiliknya
def can_access(user, acc):
    return bool(acc) and acc.get("owner_id") == user["id"]


def visible_accounts(user):
    return [a for a in list_accounts() if a.get("owner_id") == user["id"]]


def accessible_ids(user):
    return {a["id"] for a in visible_accounts(user)}


def run_accessible(user, run):
    return bool(run) and (run.get("account") or {}).get("id") in accessible_ids(user)


def owner_for_new(user):
    return user["id"] if user["id"] != "apikey" else None


# ------------------------------------------------------------------ endpoints
class SetupIn(BaseModel):
    api_key: str
    username: str
    password: str


class LoginIn(BaseModel):
    username: str
    password: str


class PasswordIn(BaseModel):
    current: str
    new: str


class UserIn(BaseModel):
    username: str
    password: str
    role: str = "user"


class UserUpdate(BaseModel):
    role: Optional[str] = None
    disabled: Optional[bool] = None
    password: Optional[str] = None


def _optional_user(request):
    return user_from_token(session_token(request))


@router.get("/api/auth/state")
def auth_state(request: Request):
    u = _optional_user(request)
    if u:
        ensure_default_account(u["id"])
    return {"setup_required": not list_users(), "user": public_user(u) if u else None}


@router.post("/api/auth/setup")
def auth_setup(body: SetupIn, request: Request, response: Response):
    require_csrf(request)
    keys = [f"setup:{request.client.host if request.client else '?'}"]
    throttle_check(keys)
    with _lock:
        if users_count():
            raise HTTPException(409, "Panel Sudah Disiapkan")
        if not config.API_KEY or not secrets.compare_digest(body.api_key, config.API_KEY):
            throttle_fail(keys)
            raise HTTPException(401, "Kunci API Salah")
        username = clean_username(body.username)
        check_password_rules(body.password)
        user = make_user(username, body.password, "admin")
        user_save(user)
        for acc in list_accounts():  # migrasi: akun lama tanpa pemilik jadi milik admin pertama
            if not acc.get("owner_id"):
                acc["owner_id"] = user["id"]
                save_account(acc)
        # riwayat lama (tanpa pemilik) ikut menjadi milik admin pertama agar tetap tampil
        db.x("UPDATE runs SET owner_id=? WHERE owner_id IS NULL", (user["id"],))
        ensure_default_account(user["id"])
    throttle_ok(keys)
    set_cookie(request, response, create_session(user["id"]))
    return {"setup_required": False, "user": public_user(user)}


@router.post("/api/auth/login")
def auth_login(body: LoginIn, request: Request, response: Response):
    require_csrf(request)
    keys = _keys(request, body.username)
    throttle_check(keys)
    user = find_by_username(body.username)
    ok = verify_password(user or _dummy_user(), body.password) and user is not None and not user.get("disabled")
    if not ok:
        throttle_fail(keys)
        raise HTTPException(401, "Nama Pengguna atau Kata Sandi Salah")
    throttle_ok(keys)
    ensure_default_account(user["id"])
    set_cookie(request, response, create_session(user["id"]))
    return {"setup_required": False, "user": public_user(user)}


@router.post("/api/auth/logout")
def auth_logout(request: Request, response: Response):
    require_csrf(request)
    for name in (COOKIE, LEGACY_COOKIE):
        if request.cookies.get(name):
            drop_session(request.cookies[name])
    response.delete_cookie(COOKIE, path="/")
    response.delete_cookie(LEGACY_COOKIE, path="/")
    return {"ok": True}


@router.post("/api/auth/password")
def auth_password(body: PasswordIn, user=Depends(current_user)):
    if user.get("synthetic"):
        raise HTTPException(400, "Tidak Tersedia untuk Akses Kunci API")
    keys = [f"pw:{user['id']}"]
    throttle_check(keys)
    if not verify_password(user, body.current):
        throttle_fail(keys)
        raise HTTPException(400, "Kata Sandi Saat Ini Salah")
    check_password_rules(body.new)
    with _lock:
        u = get_user(user["id"])
        u.update(hash_password(body.new))
        u["pw_changed_at"] = now_iso()
        user_save(u)
    invalidate_user_sessions(user["id"], keep_hash=user["session"])
    return {"ok": True}


def user_view(u):
    n = sum(1 for a in list_accounts() if a.get("owner_id") == u["id"])
    return {"id": u["id"], "username": u["username"], "role": u["role"], "disabled": bool(u.get("disabled")),
            "created_at": u.get("created_at"), "accounts": n}


@router.get("/api/users")
def users_list(user=Depends(require_admin)):
    return {"users": [user_view(u) for u in list_users()]}


@router.post("/api/users")
def users_create(body: UserIn, user=Depends(require_admin)):
    if body.role not in ("admin", "user"):
        raise HTTPException(400, "Peran Harus Admin atau Pengguna")
    username = clean_username(body.username)
    check_password_rules(body.password)
    with _lock:
        if find_by_username(username):
            raise HTTPException(400, "Nama Pengguna Sudah Dipakai")
        new = make_user(username, body.password, body.role)
        user_save(new)
    ensure_default_account(new["id"])
    return user_view(new)


@router.put("/api/users/{uid}")
def users_update(uid: str, body: UserUpdate, user=Depends(require_admin)):
    with _lock:
        target = get_user(uid)
        if not target:
            raise HTTPException(404, "Pengguna Tidak Ditemukan")
        was_active_admin = target["role"] == "admin" and not target.get("disabled")
        new_role = body.role if body.role is not None else target["role"]
        new_disabled = body.disabled if body.disabled is not None else bool(target.get("disabled"))
        if new_role not in ("admin", "user"):
            raise HTTPException(400, "Peran Harus Admin atau Pengguna")
        if was_active_admin and not (new_role == "admin" and not new_disabled):
            if len(active_admins()) <= 1:
                raise HTTPException(400, "Tidak Bisa Mengubah Admin Aktif Terakhir")
        kill = False
        if body.password is not None:
            check_password_rules(body.password)
            target.update(hash_password(body.password))
            target["pw_changed_at"] = now_iso()
            kill = True
        if new_disabled and not target.get("disabled"):
            kill = True
        target["role"] = new_role
        target["disabled"] = new_disabled
        user_save(target)
    if kill:
        invalidate_user_sessions(uid)
        _stop_login_of(uid)
    if not new_disabled:
        ensure_default_account(uid)
    return user_view(target)


@router.delete("/api/users/{uid}")
def users_delete(uid: str, user=Depends(require_admin)):
    """Hapus pengguna beserta semua akun TikTok dan datanya (tidak dipindahkan ke admin)."""
    from . import jobs
    from .runner import runner
    from .store import delete_account
    with _lock:
        target = get_user(uid)
        if not target:
            raise HTTPException(404, "Pengguna Tidak Ditemukan")
        if uid == user["id"]:
            raise HTTPException(400, "Tidak Bisa Menghapus Diri Sendiri")
        if target["role"] == "admin" and not target.get("disabled") and len(active_admins()) <= 1:
            raise HTTPException(400, "Tidak Bisa Menghapus Admin Aktif Terakhir")
        owned = [acc for acc in list_accounts() if acc.get("owner_id") == uid]
        if any(runner.account_busy(a["id"]) for a in owned):
            raise HTTPException(409, "Akun Pengguna Ini Sedang Dipakai Proses yang Berjalan")
        user_delete(uid)
    _stop_login_of(uid)
    ids = {a["id"] for a in owned}
    for aid in ids:
        jobs.drop_account(aid)
        delete_account(aid)  # akun, cookie, kontak, jadwal, meta, dan peta percakapan
    _purge_runs(ids)
    invalidate_user_sessions(uid)
    return {"ok": True, "deleted_accounts": len(ids)}


def _purge_runs(account_ids):
    """Hapus riwayat dan bukti dari akun yang dihapus."""
    from .store import delete_runs
    delete_runs(account_ids=list(account_ids))


# ------------------------------------------------------ notifikasi pribadi
DEFAULT_NOTIFY = {"discord_enabled": False, "discord_webhook": "", "telegram_enabled": False,
                  "telegram_token": "", "telegram_chat_id": "", "notify_screenshot": False}


class NotifyIn(BaseModel):
    discord_enabled: Optional[bool] = None
    discord_webhook: Optional[str] = None
    telegram_enabled: Optional[bool] = None
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    notify_screenshot: Optional[bool] = None


def user_notify(u):
    return {**DEFAULT_NOTIFY, **((u or {}).get("notify") or {})}


def _real_user(user):
    if user.get("synthetic"):
        raise HTTPException(400, "Tidak Tersedia untuk Akses Kunci API")
    return user


def notify_view(n):
    n = dict(n)
    token = n.pop("telegram_token")
    n["telegram_token_set"] = bool(token)
    n["discord_webhook_set"] = bool(n.pop("discord_webhook"))
    return n


@router.get("/api/me/notifications")
def my_notifications(user=Depends(current_user)):
    return notify_view(user_notify(_real_user(user)))


@router.put("/api/me/notifications")
def my_notifications_put(body: NotifyIn, user=Depends(current_user)):
    _real_user(user)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    for k in ("telegram_token", "discord_webhook"):
        if data.get(k) == "":
            data.pop(k)
    if "discord_webhook" in data and data["discord_webhook"] != "-" and not DISCORD_RE.match(data["discord_webhook"]):
        raise HTTPException(400, "URL Webhook Discord Tidak Valid")
    if data.get("discord_webhook") == "-":
        data["discord_webhook"] = ""
    for k in ("telegram_chat_id", "telegram_token"):
        if k in data and len(data[k]) > 200:
            raise HTTPException(400, f"{k} Terlalu Panjang")
    with _lock:
        u = get_user(user["id"])
        u["notify"] = {**user_notify(u), **data}
        user_save(u)
        result = notify_view(u["notify"])
    return result


def _test_msg():
    return "✅ Tes Notifikasi dari Bara"


@router.post("/api/me/notifications/test/discord")
def my_test_discord(user=Depends(current_user)):
    ok, err = send_discord(user_notify(_real_user(user)), _test_msg())
    if not ok:
        raise HTTPException(400, err)
    return {"ok": True}


@router.post("/api/me/notifications/test/telegram")
def my_test_telegram(user=Depends(current_user)):
    ok, err = send_telegram(user_notify(_real_user(user)), _test_msg())
    if not ok:
        raise HTTPException(400, err)
    return {"ok": True}
