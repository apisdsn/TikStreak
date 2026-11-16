"""Pengguna, sesi cookie, throttling login, dan otorisasi akses akun."""
import hashlib
import hmac
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

from . import config
from .notify import DISCORD_RE, send_discord, send_telegram
from .store import JsonStore, create_account, list_accounts, save_account

ITERATIONS = 600_000
SESSION_TTL = 7 * 24 * 3600
COOKIE = "sp_session"
CSRF_HEADER = "streak-panel"
MAX_FAILS = 5
FAIL_WINDOW = 15 * 60
LOCK_TIME = 15 * 60
USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,32}$")

users_store = JsonStore("users.json", [])
sessions_store = JsonStore("sessions.json", {})
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
        raise HTTPException(400, "Password harus 8-128 karakter")


def clean_username(name):
    name = (name or "").strip().lower()
    if not USERNAME_RE.match(name):
        raise HTTPException(400, "Username 3-32 karakter: huruf kecil, angka, titik, garis bawah, atau strip")
    return name


# --------------------------------------------------------------------- users
def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def list_users():
    return users_store.read()


def get_user(uid):
    return next((u for u in list_users() if u["id"] == uid), None)


def find_by_username(name):
    name = (name or "").strip().lower()
    return next((u for u in list_users() if u["username"] == name), None)


def active_admins():
    return [u for u in list_users() if u["role"] == "admin" and not u.get("disabled")]


def public_user(u):
    return {"id": u["id"], "username": u["username"], "role": u["role"]}


def make_user(username, password, role):
    return {"id": uuid.uuid4().hex[:8], "username": username, **hash_password(password), "role": role,
            "disabled": False, "created_at": now_iso(), "pw_changed_at": now_iso()}


def _stop_login_of(uid):
    from .login import login_session
    if login_session.active and login_session.owner_id == uid:
        login_session.stop()


def ensure_default_account(uid):
    """Setiap pengguna aktif minimal punya satu akun TikTok."""
    if not any(a.get("owner_id") == uid for a in list_accounts()):
        names = {a["name"].lower() for a in list_accounts() if a.get("owner_id") == uid}
        create_account("Utama" if "utama" not in names else "Akun 1", uid)


# ------------------------------------------------------------------ sessions
def _hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _purge(sessions):
    now = time.time()
    return {k: v for k, v in sessions.items() if v["expires"] > now}


def create_session(user_id):
    token = secrets.token_urlsafe(32)
    with _lock:
        sessions = _purge(sessions_store.read())
        sessions[_hash_token(token)] = {"user_id": user_id, "created": time.time(), "expires": time.time() + SESSION_TTL}
        sessions_store.write(sessions)
    return token


def drop_session(token):
    with _lock:
        sessions = _purge(sessions_store.read())
        sessions.pop(_hash_token(token), None)
        sessions_store.write(sessions)


def invalidate_user_sessions(user_id, keep_hash=None):
    with _lock:
        sessions = _purge(sessions_store.read())
        sessions = {k: v for k, v in sessions.items() if v["user_id"] != user_id or k == keep_hash}
        sessions_store.write(sessions)


def user_from_token(token):
    if not token:
        return None
    h = _hash_token(token)
    s = sessions_store.read().get(h)
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
                raise HTTPException(429, "Terlalu banyak percobaan gagal. Coba lagi beberapa menit lagi.")


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
    if request.headers.get("x-requested-with") != CSRF_HEADER:
        return False
    origin = request.headers.get("origin")
    if origin:
        host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
        if urlparse(origin).netloc != host and urlparse(origin).netloc != request.headers.get("host", ""):
            return False
    return True


def require_csrf(request):
    if not csrf_ok(request):
        raise HTTPException(403, "Permintaan ditolak (CSRF)")


# ---------------------------------------------------------------- dependency
API_USER = {"id": "apikey", "username": "api", "role": "admin", "synthetic": True, "session": None}


def current_user(request: Request, x_api_key: Optional[str] = Header(None)):
    if x_api_key:
        if config.API_KEY and secrets.compare_digest(x_api_key, config.API_KEY):
            return API_USER
        raise HTTPException(401, "Access key salah atau tidak ada")
    user = user_from_token(request.cookies.get(COOKIE))
    if not user:
        raise HTTPException(401, "Belum masuk")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        require_csrf(request)
    return user


def require_admin(user=Depends(current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Hanya admin yang boleh melakukan ini")
    return user


# ------------------------------------------------------------------- akses
def is_admin(user):
    return user["role"] == "admin"


def can_access(user, acc):
    return is_admin(user) or acc.get("owner_id") == user["id"]


def visible_accounts(user):
    accs = list_accounts()
    return accs if is_admin(user) else [a for a in accs if a.get("owner_id") == user["id"]]


def accessible_ids(user):
    return {a["id"] for a in visible_accounts(user)}


def run_accessible(user, run):
    if is_admin(user):
        return True
    return bool(run) and (run.get("account") or {}).get("id") in accessible_ids(user)


def owner_for_new(user):
    if not user.get("synthetic"):
        return user["id"]
    admins = active_admins()
    return admins[0]["id"] if admins else None


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
    return user_from_token(request.cookies.get(COOKIE))


@router.get("/api/auth/state")
def auth_state(request: Request):
    u = _optional_user(request)
    if u and u["role"] == "user":
        ensure_default_account(u["id"])
    return {"setup_required": not list_users(), "user": public_user(u) if u else None}


@router.post("/api/auth/setup")
def auth_setup(body: SetupIn, request: Request, response: Response):
    require_csrf(request)
    keys = [f"setup:{request.client.host if request.client else '?'}"]
    throttle_check(keys)
    with _lock:
        if list_users():
            raise HTTPException(409, "Panel sudah disiapkan")
        if not config.API_KEY or not secrets.compare_digest(body.api_key, config.API_KEY):
            throttle_fail(keys)
            raise HTTPException(401, "API key salah")
        username = clean_username(body.username)
        check_password_rules(body.password)
        user = make_user(username, body.password, "admin")
        users_store.write([user])
        for acc in list_accounts():  # migrasi: akun lama tanpa pemilik jadi milik admin pertama
            if not acc.get("owner_id"):
                acc["owner_id"] = user["id"]
                save_account(acc)
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
        raise HTTPException(401, "Username atau password salah")
    throttle_ok(keys)
    if user["role"] == "user":
        ensure_default_account(user["id"])
    set_cookie(request, response, create_session(user["id"]))
    return {"setup_required": False, "user": public_user(user)}


@router.post("/api/auth/logout")
def auth_logout(request: Request, response: Response):
    require_csrf(request)
    token = request.cookies.get(COOKIE)
    if token:
        drop_session(token)
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.post("/api/auth/password")
def auth_password(body: PasswordIn, user=Depends(current_user)):
    if user.get("synthetic"):
        raise HTTPException(400, "Tidak tersedia untuk akses API key")
    keys = [f"pw:{user['id']}"]
    throttle_check(keys)
    if not verify_password(user, body.current):
        throttle_fail(keys)
        raise HTTPException(400, "Password saat ini salah")
    check_password_rules(body.new)
    with _lock:
        users = list_users()
        for u in users:
            if u["id"] == user["id"]:
                u.update(hash_password(body.new))
                u["pw_changed_at"] = now_iso()
        users_store.write(users)
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
        raise HTTPException(400, "Role harus admin atau user")
    username = clean_username(body.username)
    check_password_rules(body.password)
    with _lock:
        if find_by_username(username):
            raise HTTPException(400, "Username sudah dipakai")
        new = make_user(username, body.password, body.role)
        users_store.write(list_users() + [new])
    ensure_default_account(new["id"])
    return user_view(new)


@router.put("/api/users/{uid}")
def users_update(uid: str, body: UserUpdate, user=Depends(require_admin)):
    with _lock:
        users = list_users()
        target = next((u for u in users if u["id"] == uid), None)
        if not target:
            raise HTTPException(404, "Pengguna tidak ditemukan")
        was_active_admin = target["role"] == "admin" and not target.get("disabled")
        new_role = body.role if body.role is not None else target["role"]
        new_disabled = body.disabled if body.disabled is not None else bool(target.get("disabled"))
        if new_role not in ("admin", "user"):
            raise HTTPException(400, "Role harus admin atau user")
        if was_active_admin and not (new_role == "admin" and not new_disabled):
            if len(active_admins()) <= 1:
                raise HTTPException(400, "Tidak bisa mengubah admin aktif terakhir")
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
        users_store.write(users)
    if kill:
        invalidate_user_sessions(uid)
        _stop_login_of(uid)
    if not new_disabled and new_role == "user":
        ensure_default_account(uid)
    return user_view(target)


@router.delete("/api/users/{uid}")
def users_delete(uid: str, reassign_to: Optional[str] = None, user=Depends(require_admin)):
    with _lock:
        users = list_users()
        target = next((u for u in users if u["id"] == uid), None)
        if not target:
            raise HTTPException(404, "Pengguna tidak ditemukan")
        if uid == user["id"]:
            raise HTTPException(400, "Tidak bisa menghapus diri sendiri")
        if target["role"] == "admin" and not target.get("disabled") and len(active_admins()) <= 1:
            raise HTTPException(400, "Tidak bisa menghapus admin aktif terakhir")
        dest_id = reassign_to or (user["id"] if not user.get("synthetic") else None)
        dest = get_user(dest_id) if dest_id else None
        if dest is None and user.get("synthetic"):
            dest = active_admins()[0] if active_admins() else None
        if not dest or dest.get("disabled") or dest["role"] != "admin" or dest["id"] == uid:
            raise HTTPException(400, "Tujuan pemindahan akun harus admin aktif lain")
        for acc in list_accounts():
            if acc.get("owner_id") == uid:
                acc["owner_id"] = dest["id"]
                save_account(acc)
        users_store.write([u for u in users if u["id"] != uid])
    invalidate_user_sessions(uid)
    _stop_login_of(uid)
    return {"ok": True, "reassigned_to": dest["id"]}


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
        raise HTTPException(400, "Tidak tersedia untuk akses API key")
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
        raise HTTPException(400, "URL webhook Discord tidak valid")
    if data.get("discord_webhook") == "-":
        data["discord_webhook"] = ""
    for k in ("telegram_chat_id", "telegram_token"):
        if k in data and len(data[k]) > 200:
            raise HTTPException(400, f"{k} terlalu panjang")
    with _lock:
        users = list_users()
        for u in users:
            if u["id"] == user["id"]:
                u["notify"] = {**user_notify(u), **data}
                result = notify_view(u["notify"])
        users_store.write(users)
    return result


def _test_msg():
    return "✅ Tes notifikasi dari TikTok Streak Panel"


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
