"""Sidik jari browser yang konsisten: UA, client hints, dan platform harus saling cocok.

Chromium di Linux yang dikontrol lewat CDP melaporkan UA "Windows" jika dipaksa
lewat konfigurasi lama, sedangkan platform dan Sec-CH-UA tetap Linux. Ketidakcocokan
itu membuat TikTok menolak aksi verifikasi. Modul ini membangun satu UA dari versi
browser yang sebenarnya dan memakainya di browser login maupun browser pengirim.
"""
import re
import subprocess

from . import config

_version = None


def real_version():
    """Versi lengkap browser (mis. 131.0.6778.204) dari `browser --version`."""
    global _version
    if _version:
        return _version
    try:
        out = subprocess.run([config.BROWSER_PATH, "--version"], capture_output=True, text=True, timeout=10).stdout
        m = re.search(r"(\d+\.\d+\.\d+\.\d+)", out)
        _version = m.group(1) if m else "131.0.0.0"
    except Exception:  # noqa: BLE001
        _version = "131.0.0.0"
    return _version


def build_ua():
    """UA Chrome Linux standar (versi dipersingkat seperti Chrome asli)."""
    if config.USER_AGENT:
        return config.USER_AGENT
    major = real_version().split(".")[0]
    return (f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{major}.0.0.0 Safari/537.36")


def ua_metadata():
    full = real_version()
    major = full.split(".")[0]
    brands = [{"brand": "Chromium", "version": major}, {"brand": "Google Chrome", "version": major},
              {"brand": "Not_A Brand", "version": "24"}]
    return {
        "brands": brands,
        "fullVersionList": [{"brand": b["brand"], "version": full if b["brand"] != "Not_A Brand" else "24.0.0.0"} for b in brands],
        "fullVersion": full,
        "platform": "Linux", "platformVersion": "6.1.0", "architecture": "x86", "model": "",
        "mobile": False, "bitness": "64", "wow64": False,
    }


def apply_fingerprint(tab):
    """Setel UA + client hints + platform lewat CDP untuk satu tab. Tidak pernah melempar."""
    try:
        tab.run_cdp("Emulation.setUserAgentOverride", userAgent=build_ua(), acceptLanguage="en-US,en;q=0.9",
                    platform="Linux x86_64", userAgentMetadata=ua_metadata())
    except Exception:  # noqa: BLE001
        pass
