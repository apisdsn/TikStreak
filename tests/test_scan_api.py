import time

import pytest


def wait(pred, secs=15):
    t = time.time()
    while time.time() - t < secs:
        v = pred()
        if v:
            return v
        time.sleep(0.2)
    raise AssertionError("timeout")


@pytest.fixture
def scan_account(app_mods, user, client):
    c, u = user("scanown1")
    aid = c.get("/api/status").json()["accounts"][0]["id"]
    app_mods.store.stores(aid).cookies.write([{"name": "sessionid", "value": "x", "domain": ".tiktok.com"}])
    app_mods.store.stores(aid).contacts.write(["Rina"])
    yield c, u, aid
    client.runner.scan_executor = None


def test_scan_import_flow(scan_account, client, app_mods):
    c, u, aid = scan_account
    found = [{"id": "c1", "nick": "Rina", "time": "08:01"}, {"id": "c2", "nick": "Dimas", "time": "09:30"}, {"id": "c3", "nick": "Sari", "time": "10:02"}]
    client.runner.scan_executor = lambda job, cancel, prov: found
    assert c.get(f"/api/contacts/scan?account={aid}").json()["state"] == "none"
    r = c.post(f"/api/contacts/scan?account={aid}")
    assert r.status_code == 200
    res = wait(lambda: (lambda v: v if v["state"] in ("done", "failed") else None)(c.get(f"/api/contacts/scan?account={aid}").json()))
    assert res["state"] == "done"
    by = {i["nick"]: i for i in res["items"]}
    assert by["Rina"]["exists"] is True and by["Dimas"]["exists"] is False and by["Dimas"]["time"] == "09:30"
    assert 0 < res["expires_in"] <= 3600
    r = c.post(f"/api/contacts/import?account={aid}", json={"ids": ["c1", "c2", "c3", "nope"]})
    assert r.status_code == 200 and r.json()["added"] == ["Dimas", "Sari"]  # yang sudah ada dan id asing dilewati
    st = app_mods.store.stores(aid)
    assert st.contacts.read() == ["Rina", "Dimas", "Sari"]
    assert st.convs.read()["dimas"] == "c2" and st.convs.read()["sari"] == "c3"  # id percakapan tersimpan
    assert c.post(f"/api/contacts/import?account={aid}", json={"ids": ["c2"]}).status_code == 400  # tidak ada yang baru


def test_scan_requires_cookie_and_is_private(user, client, app_mods, scan_account):
    c, u, aid = scan_account
    other, ou = user("scanoth1")
    assert other.post(f"/api/contacts/scan?account={aid}").status_code == 404  # akun orang lain
    assert other.get(f"/api/contacts/scan?account={aid}").status_code == 404
    oaid = other.get("/api/status").json()["accounts"][0]["id"]
    assert other.post(f"/api/contacts/scan?account={oaid}").status_code == 400  # belum ada cookie


def test_scan_failure_reported_and_results_expire(scan_account, client, app_mods, monkeypatch):
    c, u, aid = scan_account
    def boom(job, cancel, prov):
        raise RuntimeError("Browser Tidak Ditemukan")
    client.runner.scan_executor = boom
    c.post(f"/api/contacts/scan?account={aid}")
    res = wait(lambda: (lambda v: v if v["state"] in ("done", "failed") else None)(c.get(f"/api/contacts/scan?account={aid}").json()))
    assert res["state"] == "failed" and "Browser" in res["error"]
    assert c.post(f"/api/contacts/import?account={aid}", json={"ids": ["x"]}).status_code == 404
    # hasil kedaluwarsa setelah 1 jam
    app_mods.store.scan_set(aid, [{"id": "c9", "nick": "Z", "time": ""}])
    assert c.get(f"/api/contacts/scan?account={aid}").json()["state"] == "done"
    v = app_mods.store.kv_get("scan:" + aid)
    v["at"] -= 3601
    app_mods.store.kv_set("scan:" + aid, v)
    assert c.get(f"/api/contacts/scan?account={aid}").json()["state"] == "none"
    assert app_mods.store.kv_get("scan:" + aid) is None  # dihapus dari db


def test_scan_job_not_in_history_or_notifications(scan_account, client, app_mods, sent):
    c, u, aid = scan_account
    client.runner.scan_executor = lambda job, cancel, prov: [{"id": "c1", "nick": "Rahasia", "time": ""}]
    before = app_mods.db.q1("SELECT COUNT(*) n FROM runs WHERE account_id=?", (aid,))["n"]
    c.post(f"/api/contacts/scan?account={aid}")
    wait(lambda: c.get(f"/api/contacts/scan?account={aid}").json()["state"] == "done")
    assert app_mods.db.q1("SELECT COUNT(*) n FROM runs WHERE account_id=?", (aid,))["n"] == before
    assert sent == []
