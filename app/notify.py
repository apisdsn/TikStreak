import re

import requests

DISCORD_RE = re.compile(r"^https://(?:ptb\.|canary\.)?(?:discord|discordapp)\.com/api/webhooks/\d+/[\w-]+$")


def send_telegram(settings, text):
    """Kirim pesan Telegram (HTML). Return (ok, error)."""
    token = settings.get("telegram_token")
    chat_id = settings.get("telegram_chat_id")
    if not token or not chat_id:
        return False, "Token atau Chat ID belum diisi"
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        if r.status_code == 200:
            return True, None
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def send_discord(settings, text):
    """Kirim pesan ke Discord webhook (markdown). Return (ok, error)."""
    url = settings.get("discord_webhook")
    if not url:
        return False, "Webhook URL belum diisi"
    try:
        r = requests.post(url, json={"content": text[:1900], "username": "Streak Panel"}, timeout=10)
        if r.status_code in (200, 204):
            return True, None
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def notify(settings, title, lines=()):
    """Kirim ke semua kanal yang aktif. title/lines berupa teks polos."""
    body = "\n".join(lines)
    if settings.get("telegram_enabled"):
        send_telegram(settings, f"<b>{title}</b>" + (f"\n{body}" if body else ""))
    if settings.get("discord_enabled"):
        send_discord(settings, f"**{title}**" + (f"\n{body}" if body else ""))
