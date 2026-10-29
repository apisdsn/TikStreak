import os

DATA_DIR = os.getenv("DATA_DIR", "/data")
API_KEY = os.getenv("API_KEY", "")
DEFAULT_TZ = os.getenv("TZ", "UTC")
BROWSER_PATH = os.getenv("BROWSER_PATH", "/usr/bin/chromium")
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
)
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

TIKTOK_URL = "https://www.tiktok.com"
TIKTOK_MESSAGES_URL = "https://www.tiktok.com/messages"

os.makedirs(DATA_DIR, exist_ok=True)
