"""Penyimpanan JSON sederhana di DATA_DIR (atomic write + lock)."""
import json
import os
import threading

from .config import DATA_DIR

DEFAULT_SETTINGS = {
    "message": "🔥 Streak 🔥",
    "schedule_enabled": False,
    "schedule_time": "00:00",
    "timezone": "",
    "telegram_enabled": False,
    "telegram_token": "",
    "telegram_chat_id": "",
    "discord_enabled": False,
    "discord_webhook": "",
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
contacts_store = JsonStore("contacts.json", [])
cookies_store = JsonStore("cookies.json", [])
history_store = JsonStore("history.json", [])
meta_store = JsonStore("meta.json", {})


def get_settings():
    data = settings_store.read()
    return {**DEFAULT_SETTINGS, **data}
