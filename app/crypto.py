"""Enkripsi rahasia (cookie, webhook, token) saat disimpan di database (AES-256-GCM)."""
import base64
import hashlib
import logging
import os
import secrets
import threading

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import config

log = logging.getLogger("bara")
_key = None
_lock = threading.Lock()


def _load_key():
    global _key
    with _lock:
        if _key:
            return _key
        if config.SECRET_KEY:
            _key = hashlib.sha256(config.SECRET_KEY.encode("utf-8")).digest()
            return _key
        path = os.path.join(config.DATA_DIR, "secret.key")
        if os.path.exists(path):
            with open(path, "rb") as f:
                _key = base64.b64decode(f.read().strip())
            return _key
        _key = secrets.token_bytes(32)
        os.makedirs(config.DATA_DIR, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(base64.b64encode(_key))
        log.warning("SECRET_KEY belum diatur: kunci enkripsi dibuat di %s. Atur SECRET_KEY di .env dan "
                    "simpan cadangannya; tanpa kunci ini cookie tidak bisa dibaca.", path)
        return _key


def encrypt(data):
    """bytes/str -> bytes (nonce 12 byte + ciphertext)."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    nonce = secrets.token_bytes(12)
    return nonce + AESGCM(_load_key()).encrypt(nonce, data, None)


def decrypt(blob):
    blob = bytes(blob)
    return AESGCM(_load_key()).decrypt(blob[:12], blob[12:], None)


def enc_text(text):
    """str -> 'enc:<base64>' untuk disimpan di kolom teks; string kosong tetap kosong."""
    if not text:
        return ""
    return "enc:" + base64.b64encode(encrypt(text)).decode()


def dec_text(value):
    if not value or not str(value).startswith("enc:"):
        return value or ""
    return decrypt(base64.b64decode(value[4:])).decode("utf-8")
