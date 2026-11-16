import os

DATA_DIR = os.getenv("DATA_DIR", "/data")
API_KEY = os.getenv("API_KEY", "")
DEFAULT_TZ = os.getenv("TZ", "UTC")
BROWSER_PATH = os.getenv("BROWSER_PATH", "/usr/bin/chromium")
# Kosong = pakai UA asli browser (tanpa "Headless") yang konsisten dengan platform; isi untuk menimpa
USER_AGENT = os.getenv("USER_AGENT", "")
# Hanya untuk pengujian: halaman awal sesi login remote
LOGIN_START_URL = os.getenv("LOGIN_START_URL", "")
TRUST_PROXY = os.getenv("TRUST_PROXY", "0").lower() in ("1", "true", "yes")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

TIKTOK_URL = "https://www.tiktok.com"
TIKTOK_MESSAGES_URL = "https://www.tiktok.com/messages"

os.makedirs(DATA_DIR, exist_ok=True)
