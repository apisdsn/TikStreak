"""Penyimpanan JSON sederhana di DATA_DIR (atomic write + lock)."""
import json
import os
import shutil
import threading
import uuid

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


class JsonStore:
    def __init__(self, name, default):
        self.path = os.path.join(DATA_DIR, name)
        self.default = default
        self._lock = threading.RLock()

    def read(self):
        with self._lock:
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return json.loads(json.dumps(self.default))

    def write(self, data):
        with self._lock:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
            try:
                os.chmod(self.path, 0o600)
            except OSError:
                pass

    def delete(self):
        with self._lock:
            try:
                os.remove(self.path)
            except FileNotFoundError:
                pass


settings_store = JsonStore("settings.json", DEFAULT_SETTINGS)
history_store = JsonStore("history.json", [])
accounts_store = JsonStore("accounts.json", [])


def get_settings():
    data = settings_store.read()
    for legacy in ("schedules", "schedule_enabled", "schedule_time"):
        data.pop(legacy, None)  # jadwal kini per akun
    return {**DEFAULT_SETTINGS, **data}


# ------------------------------------------------------------------ akun
class AccountStores:
    """Penyimpanan milik satu akun: cookie, kontak, dan metadata (status cookie, jadwal terkirim)."""

    def __init__(self, aid):
        base = f"accounts/{aid}"
        self.cookies = JsonStore(f"{base}/cookies.json", [])
        self.contacts = JsonStore(f"{base}/contacts.json", [])
        self.meta = JsonStore(f"{base}/meta.json", {})


_stores = {}
_stores_lock = threading.Lock()


def stores(aid):
    with _stores_lock:
        if aid not in _stores:
            _stores[aid] = AccountStores(aid)
        return _stores[aid]


def list_accounts():
    return accounts_store.read()


def get_account(aid):
    for a in list_accounts():
        if a["id"] == aid:
            return a
    return None


def save_account(acc):
    accs = list_accounts()
    for i, a in enumerate(accs):
        if a["id"] == acc["id"]:
            accs[i] = acc
            break
    else:
        accs.append(acc)
    accounts_store.write(accs)


def create_account(name):
    acc = {"id": uuid.uuid4().hex[:6], "name": name, "schedules": []}
    save_account(acc)
    return acc


def delete_account(aid):
    accounts_store.write([a for a in list_accounts() if a["id"] != aid])
    shutil.rmtree(os.path.join(DATA_DIR, "accounts", aid), ignore_errors=True)
    with _stores_lock:
        _stores.pop(aid, None)


def migrate_legacy():
    """Pindahkan data format lama (satu akun) ke akun "Utama". Aman dipanggil berulang."""
    if os.path.exists(accounts_store.path):
        return
    raw = settings_store.read()
    schedules = raw.get("schedules")
    if schedules is None and "schedule_time" in raw:
        schedules = [{
            "id": "s1",
            "enabled": bool(raw.get("schedule_enabled", False)),
            "time": raw["schedule_time"],
            "message": "",
        }]
    accounts_store.write([{"id": "main", "name": "Utama", "schedules": schedules or []}])
    dest = os.path.join(DATA_DIR, "accounts", "main")
    os.makedirs(dest, exist_ok=True)
    for name in ("cookies.json", "contacts.json", "meta.json"):
        src = os.path.join(DATA_DIR, name)
        if os.path.exists(src):
            shutil.move(src, os.path.join(dest, name))


migrate_legacy()
