from conftest import needs_browser


def test_json_migration(run_script):
    run_script("migtest.py")


def test_queue(run_script):
    run_script("queuetest.py")


def test_notifications(run_script):
    run_script("notiftest.py")


@needs_browser
def test_login_session_limit(make_server, run_script):
    srv = make_server("legacy", {"LOGIN_SESSIONS": "1", "LOGIN_START_URL": "about:blank"})
    run_script("logintest2.py", srv)


@needs_browser
def test_login_browser_and_fingerprint(run_script):
    run_script("logintest.py")


@needs_browser
def test_browser_pool(run_script):
    run_script("pooltest.py")
