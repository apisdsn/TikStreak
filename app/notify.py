import html
import json
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


def send_discord(settings, text, files=()):
    """Kirim ke Discord webhook (markdown) dengan lampiran opsional [(nama, bytes)]."""
    url = settings.get("discord_webhook")
    if not url:
        return False, "Webhook URL belum diisi"
    payload = {"content": text[:1900], "username": "Streak Panel"}
    try:
        if files:
            r = requests.post(
                url,
                data={"payload_json": json.dumps(payload)},
                files={f"files[{i}]": (n, b, "image/jpeg") for i, (n, b) in enumerate(files[:10])},
                timeout=30,
            )
        else:
            r = requests.post(url, json=payload, timeout=10)
        if r.status_code in (200, 204):
            return True, None
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def send_telegram_photos(settings, files):
    token, chat_id = settings.get("telegram_token"), settings.get("telegram_chat_id")
    files = list(files)[:10]
    if not token or not chat_id or not files:
        return False, "Tidak ada yang dikirim"
    try:
        media = [{"type": "photo", "media": f"attach://p{i}", "caption": n[:200]} for i, (n, _) in enumerate(files)]
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMediaGroup",
            data={"chat_id": chat_id, "media": json.dumps(media)},
            files={f"p{i}": (f"{i}.jpg", b, "image/jpeg") for i, (_, b) in enumerate(files)},
            timeout=30,
        )
        return (True, None) if r.status_code == 200 else (False, f"HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def notify(settings, title, lines=(), files=()):
    """Kirim ke semua kanal aktif. title/lines teks polos; files = [(caption, jpeg_bytes)]."""
    body = "\n".join(lines)
    files = list(files)
    if settings.get("telegram_enabled"):
        send_telegram(settings, f"<b>{html.escape(title)}</b>" + (f"\n{html.escape(body)}" if body else ""))
        if files:
            send_telegram_photos(settings, files)
    if settings.get("discord_enabled"):
        send_discord(settings, f"**{title}**" + (f"\n{body}" if body else ""), files)
