import os
import subprocess
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests", "support"))
from server import Server, chromium_path  # noqa: E402

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
