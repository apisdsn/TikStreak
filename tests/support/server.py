"""Menjalankan aplikasi uvicorn pada port bebas dengan folder data sementara (dipakai fixture pytest)."""
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))
import seed  # noqa: E402


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def chromium_path():
    p = os.environ.get("BROWSER_PATH")
    if p:
        return p
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            return pw.chromium.executable_path
    except Exception:  # noqa: BLE001
        return ""


class Server:
    def __init__(self, profile="legacy", env=None, tmp=None):
        self.tmp = tmp or tempfile.mkdtemp(prefix="bara-test-")
        self.data = os.path.join(self.tmp, "data")
        os.makedirs(self.data, exist_ok=True)
        if profile == "legacy":
            seed.legacy(self.data)
        self.env = {"QUEUE_JITTER_MIN": "0", "QUEUE_JITTER_MAX": "1", **(env or {})}
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.proc = None

    def start(self, extra=None):
        env = {**os.environ, "DATA_DIR": self.data, "API_KEY": "testkey123", "BROWSER_PATH": chromium_path(), **self.env, **(extra or {})}
        self.log = open(os.path.join(self.tmp, "server.log"), "w")
        self.proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(self.port), "--host", "127.0.0.1"],
                                     cwd=ROOT, env=env, stdout=self.log, stderr=subprocess.STDOUT)
        for _ in range(100):
            try:
                urllib.request.urlopen(self.base + "/api/health", timeout=1)
                return self
            except Exception:  # noqa: BLE001
                time.sleep(0.2)
        raise RuntimeError("server tidak naik")

    def stop(self):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            self.proc = None

    def cleanup(self):
        self.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def prepare(self, profile):
        subprocess.run([sys.executable, os.path.join(ROOT, "tests", "support", "prepare.py"), self.base, profile], check=True)
