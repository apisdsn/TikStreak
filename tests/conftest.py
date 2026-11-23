import os
import subprocess
import sys
import tempfile

import pytest

# tes in-process memakai folder data sementara bersama; harus diatur sebelum modul app diimpor
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="bara-inproc-"))
os.environ.setdefault("API_KEY", "testkey123")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))
from server import Server, chromium_path  # noqa: E402

import itertools
_counter = itertools.count(1)
SCRIPTS = os.path.join(ROOT, "tests", "scripts")


@pytest.fixture
def make_server():
    made = []

    def make(profile="legacy", env=None):
        s = Server(profile, env)
        made.append(s)
        return s.start()

    yield make
    for s in made:
        s.cleanup()


@pytest.fixture
def run_script():
    """Jalankan skrip tes mandiri (tests/scripts) dan gagal bila keluarannya memuat FAIL atau kode keluar != 0."""
    def run(name, server=None, extra_env=None, timeout=600):
        tmp = tempfile.mkdtemp(prefix="bara-script-")
        env = {**os.environ, "BARA_TMP": tmp, "BROWSER_PATH": chromium_path(), **(extra_env or {})}
        if server:
            env.update(BARA_BASE=server.base, BARA_DATA=server.data)
        p = subprocess.run([sys.executable, os.path.join(SCRIPTS, name)], env=env, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
        bad = [l for l in p.stdout.splitlines() if l.startswith("FAIL ")]
        assert p.returncode == 0 and not bad, f"{name} gagal:\n" + "\n".join(bad) + "\n" + p.stdout[-1500:] + p.stderr[-1500:]
        return p.stdout
    return run


needs_browser = pytest.mark.skipif(not chromium_path() or not os.path.exists(chromium_path() or ""), reason="Chromium tidak tersedia")


@pytest.fixture(scope="session")
def app_mods():
    """Modul aplikasi untuk tes in-process (satu DATA_DIR sementara untuk seluruh sesi)."""
    sys.path.insert(0, ROOT)
    from app import auth, db, jobs, notify as N, runner as R, store
    return type("M", (), {"auth": auth, "db": db, "jobs": jobs, "N": N, "R": R, "store": store})


@pytest.fixture
def sent(monkeypatch, app_mods):
    """Tangkap semua notifikasi yang dikirim Runner: daftar (judul, baris)."""
    out = []
    def fake(cfg, title, lines=(), files=None):
        out.append({"title": title, "lines": list(lines), "discord": cfg.get("discord_webhook") if cfg.get("discord_enabled") else None,
                    "telegram": cfg.get("telegram_chat_id") if cfg.get("telegram_enabled") else None})
        return True
    monkeypatch.setattr(app_mods.R, "notify", fake)
    return out


@pytest.fixture(scope="module")
def client(app_mods):
    """TestClient in-process (worker dan scheduler berjalan). Gunakan user() untuk membuat pengguna masuk."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.runner import runner
    with TestClient(app, base_url="http://localhost") as c:
        c.runner = runner
        runner.jitter = (0, 0)  # tanpa jeda acak antar job agar tes cepat

        def fake_exec(run, job, cancel, get_provider):  # jadwal akun lain dari tes sebelumnya tidak boleh membuka browser sungguhan
            run.update(status="success", sent=0, total=0, results=[])
        runner.executor = fake_exec
        yield c


@pytest.fixture
def user(app_mods, client):
    """Fabrik: user('nama') -> (TestClient terpisah yang sudah login, data user)."""
    from fastapi.testclient import TestClient
    from app.main import app
    made = []

    def make(name, role="user"):
        name = f"{name}{next(_counter)}"  # nama unik: DB in-process dipakai bersama antar tes
        u = app_mods.auth.make_user(name, "password1", role)
        app_mods.store.user_save(u)
        c = TestClient(app, base_url="http://localhost", headers={"X-Requested-With": "bara"})
        r = c.post("/api/auth/login", json={"username": name, "password": "password1"})
        assert r.status_code == 200, r.text
        made.append(c)
        return c, u
    return make
