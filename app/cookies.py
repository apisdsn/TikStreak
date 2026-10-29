"""Parsing & normalisasi cookie TikTok dari berbagai format ekspor."""
import json

KEEP = ("name", "value", "domain", "path", "secure", "httpOnly")


def parse_cookies(raw):
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Cookie kosong")

    items = None
    if raw[0] in "[{":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON tidak valid: {e}") from e
        if isinstance(data, dict):
            data = data.get("cookies", [data])
        items = data
    else:
        # Format header "a=b; c=d"
        items = []
        for part in raw.split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                items.append({"name": k.strip(), "value": v.strip()})

    cookies = []
    for c in items:
        if not isinstance(c, dict) or not c.get("name"):
            continue
        out = {k: c[k] for k in KEEP if k in c}
        out["value"] = str(out.get("value", ""))
        out.setdefault("domain", ".tiktok.com")
        out.setdefault("path", "/")
        cookies.append(out)

    if not cookies:
        raise ValueError("Tidak ada cookie yang dapat dibaca")
    return cookies


def summary(cookies):
    names = {c.get("name") for c in cookies}
    return {
        "present": bool(cookies),
        "count": len(cookies),
        "has_session": "sessionid" in names,
    }
