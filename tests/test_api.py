def test_api_flow(make_server, run_script):
    """Setup, CSRF, kepemilikan akun, antrean, notifikasi per pengguna, riwayat berhalaman, dasbor."""
    srv = make_server("legacy")
    run_script("apitest.py", srv)


def test_login_lockout(make_server, run_script):
    srv = make_server("legacy")
    srv.prepare("setup")
    import requests
    H = {"X-Requested-With": "bara"}
    requests.post(srv.base + "/api/users", json={"username": "bob", "password": "bobpass123", "role": "user"}, headers=H)
    run_script("lockout.py", srv)


def test_encryption_at_rest(make_server, run_script):
    srv = make_server("legacy")
    run_script("enctest.py", srv)
