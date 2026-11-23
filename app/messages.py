"""Pemilihan teks pesan per kontak: pesan jadwal > variasi akun > pesan default, dengan placeholder dan emoji acak."""
import hashlib
from datetime import date, timedelta

EMOJIS = ("🔥", "✨", "💫", "⚡", "🌟")
MAX_VARIATIONS = 20
MAX_LENGTH = 500


def _pick(seed, n):
    return int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16) % n


def day_number(state, today):
    """Hari ke-berapa pesan ini bagi kontak: streak + 1. Stabil sepanjang hari (percobaan ulang menghasilkan angka yang sama)."""
    if not state or not state.get("streak_date"):
        return 1
    if state["streak_date"] == today:
        return state["streak_days"]  # hari ini sudah tercatat dalam streak
    yesterday = (date.fromisoformat(today) - timedelta(days=1)).isoformat()
    return state["streak_days"] + 1 if state["streak_date"] == yesterday else 1


def render(template, name, day):
    return template.replace("{nama}", name).replace("{hari}", str(day))


def resolve(settings, account, contact, override, today, state=None):
    """Teks yang dikirim ke satu kontak pada tanggal `today` (YYYY-MM-DD). Deterministik: akun + kontak + tanggal."""
    seed = f"{account['id']}|{contact.strip().lower()}|{today}"
    variations = [v for v in (account.get("variations") or []) if v and v.strip()]
    if override and override.strip():
        base = override.strip()
    elif variations:
        base = variations[_pick(seed, len(variations))]
    else:
        base = settings["message"]
    text = render(base, contact, day_number(state, today))
    if account.get("random_emoji"):
        text += " " + EMOJIS[_pick(seed + "|emoji", len(EMOJIS))]
    return text
