import os

DATA_DIR = os.getenv("DATA_DIR", "/data")
API_KEY = os.getenv("API_KEY", "")
DEFAULT_TZ = os.getenv("TZ", "UTC")
BROWSER_PATH = os.getenv("BROWSER_PATH", "/usr/bin/chromium")
# Kosong = pakai UA asli browser (tanpa "Headless") yang konsisten dengan platform; isi untuk menimpa
USER_AGENT = os.getenv("USER_AGENT", "")
# Hanya untuk pengujian: halaman awal sesi login remote
LOGIN_START_URL = os.getenv("LOGIN_START_URL", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")


def _int(name, default, lo=None, hi=None):
    try:
        v = int(os.getenv(name, default))
    except ValueError:
        v = default
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return v


HISTORY_DAYS = _int("HISTORY_DAYS", 90, 1)
HISTORY_PER_ACCOUNT = _int("HISTORY_PER_ACCOUNT", 1000, 10)
MAX_ACCOUNTS = _int("MAX_ACCOUNTS", 100, 1)
MAX_ACCOUNTS_PER_USER = _int("MAX_ACCOUNTS_PER_USER", 5, 1)
MAX_ACCOUNTS_PER_ADMIN = _int("MAX_ACCOUNTS_PER_ADMIN", 10, 1)
BROWSER_WORKERS = _int("BROWSER_WORKERS", 1, 1, 4)
LOGIN_SESSIONS = _int("LOGIN_SESSIONS", 1, 1, 3)
QUEUE_JITTER_MIN = _int("QUEUE_JITTER_MIN", 5, 0)
QUEUE_JITTER_MAX = max(QUEUE_JITTER_MIN, _int("QUEUE_JITTER_MAX", 20, 0))
BROWSER_RECYCLE_JOBS = _int("BROWSER_RECYCLE_JOBS", 25, 1)
BROWSER_MAX_MB = _int("BROWSER_MAX_MB", 700, 100)
BROWSER_KIND = os.getenv("BROWSER_KIND", "auto").lower()  # auto | full | shell
SHELL_PATH = os.getenv("BROWSER_SHELL_PATH", "")
LANDING_ENABLED = os.getenv("LANDING_ENABLED", "1").lower() not in ("0", "false", "no", "off")
LANDING_DOCS_URL = os.getenv("LANDING_DOCS_URL", "").strip()
RETRY_DELAY_MIN = _int("RETRY_DELAY_MIN", 30, 1, 240)
RETRY_MAX = _int("RETRY_MAX", 2, 0, 5)
SCAN_MAX = _int("SCAN_MAX", 200, 10, 1000)
HEALTHCHECK_PING_URL = os.getenv("HEALTHCHECK_PING_URL", "").strip()
TRUST_PROXY = os.getenv("TRUST_PROXY", "0").lower() in ("1", "true", "yes")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

TIKTOK_URL = "https://www.tiktok.com"
TIKTOK_MESSAGES_URL = "https://www.tiktok.com/messages"

os.makedirs(DATA_DIR, exist_ok=True)
