import threading
import time
import http.server
from datetime import datetime, timedelta

import pytest
import requests


def mk_owner(m, name, role="user", discord=None):
    u = m.auth.make_user(name, "password1", role)
    if discord:
        u["notify"] = {"discord_enabled": True, "discord_webhook": discord}
    m.store.user_save(u)
    return u


def mk_account(m, aid, owner, schedules=True, cookies=True):
    sched = [{"id": "s" + aid, "enabled": True, "time": "07:00", "message": "", "contacts": None}] if schedules else []
    m.store.save_account({"id": aid, "name": "Akun " + aid, "owner_id": owner["id"], "schedules": sched})
    if cookies:
        m.store.stores(aid).cookies.write([{"name": "sessionid", "value": "x", "domain": ".tiktok.com"}])


def failed_run(aid, errors, **kw):
    return {"id": "r" + aid, "account": {"id": aid, "name": "Akun " + aid}, "mode": "send", "trigger": "schedule", "status": "failed",
            "started_at": "2026-11-16T07:00:00", "finished_at": "2026-11-16T07:00:30", "sent": 0, "total": len(errors),
            "results": [{"contact": f"orang{i}", "ok": False, "error": e} for i, e in enumerate(errors)], **kw}


GLOBAL = {"discord_enabled": True, "discord_webhook": "https://GLOBAL", "telegram_enabled": False, "message": "x"}


def test_breakage_alerts_owner_and_global_with_cooldown(app_mods, sent):
    m = app_mods
    owner = mk_owner(m, "ownbrk1", discord="https://OWN1")
    mk_account(m, "brk1", owner)
    r = m.R.Runner()
    run = failed_run("brk1", ["Pesan Tidak Terverifikasi Terkirim (Cek Screenshot)", "Kolom Pesan Tidak Ditemukan"])
    r._breakage_alert(GLOBAL, run)
    own = [x for x in sent if x["discord"] == "https://OWN1"]
    sysm = [x for x in sent if x["discord"] == "https://GLOBAL"]
    assert own and own[0]["title"] == "🛠️ Semua Kontak Gagal, Kemungkinan Tampilan TikTok Berubah"
    assert sysm and "Sistem" in sysm[0]["title"]
    blob = " ".join(sysm[0]["lines"]) + sysm[0]["title"]
    assert "orang0" not in blob and "brk1" not in blob and "Akun brk1" not in blob  # tanpa nama akun atau kontak
    n = len(sent)
    r._breakage_alert(GLOBAL, run)
    assert len(sent) == n  # jeda 6 jam


def test_breakage_not_raised_for_contact_specific_or_cookie_or_partial(app_mods, sent):
    m = app_mods
    owner = mk_owner(m, "ownbrk2", discord="https://OWN2")
    mk_account(m, "brk2", owner)
    r = m.R.Runner()
    r._breakage_alert(GLOBAL, failed_run("brk2", ["Kontak Tidak Ditemukan di Daftar Pesan"]))
    r._breakage_alert(GLOBAL, failed_run("brk2", ["x"], cookie_invalid=True))
    run = failed_run("brk2", ["x", "y"])
    run["results"][0]["ok"] = True
    r._breakage_alert(GLOBAL, run)
    assert sent == []


def test_global_alert_skipped_when_owner_already_uses_that_channel(app_mods, sent):
    m = app_mods
    admin = mk_owner(m, "admbrk3", role="admin", discord="https://GLOBAL")
    mk_account(m, "brk3", admin)
    m.store.kv_set("brk-sys", 0)
    r = m.R.Runner()
    r._breakage_alert(GLOBAL, failed_run("brk3", ["Teks Tidak Masuk ke Kolom Pesan"]))
    assert len([x for x in sent if x["discord"] == "https://GLOBAL"]) == 1  # hanya alert pemilik, tanpa duplikat sistem


def test_no_success_in_24h_alert_once_per_day(app_mods, sent):
    m = app_mods
    owner = mk_owner(m, "ownstl1", discord="https://OWNSTL")
    mk_account(m, "stl1", owner)
    old = (datetime.now() - timedelta(days=2)).isoformat(timespec="seconds")
    m.db.x("UPDATE accounts SET created_at=? WHERE id='stl1'", (old,))
    r = m.R.Runner()
    r.check_stalled()
    mine = [x for x in sent if x["discord"] == "https://OWNSTL"]
    assert len(mine) == 1 and mine[0]["title"] == "⚠️ Belum Ada Pesan Terkirim dalam 24 Jam"
    r.check_stalled()
    assert len([x for x in sent if x["discord"] == "https://OWNSTL"]) == 1  # sekali sehari


def test_no_success_alert_conditions(app_mods, sent):
    m = app_mods
    owner = mk_owner(m, "ownstl2", discord="https://OWNSTL2")
    old = (datetime.now() - timedelta(days=2)).isoformat(timespec="seconds")
    for aid, kw in (("stl2a", {"schedules": False}), ("stl2b", {"cookies": False}), ("stl2c", {})):
        mk_account(m, aid, owner, **kw)
        m.db.x("UPDATE accounts SET created_at=? WHERE id=?", (old, aid))
    # stl2c punya kiriman sukses 1 jam lalu -> tidak ada alert
    m.store.insert_run({"id": "ok00stl2", "account": {"id": "stl2c", "name": "c"}, "owner_id": owner["id"], "mode": "send", "trigger": "schedule", "status": "success",
                        "started_at": (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds"), "finished_at": None, "sent": 1, "total": 1, "results": [], "logs": []})
    m.R.Runner().check_stalled()
    assert not [x for x in sent if x["discord"] == "https://OWNSTL2"]
    # akun baru (dibuat < 24 jam) tanpa kiriman juga tidak diperingatkan
    mk_account(m, "stl2d", owner)
    m.R.Runner().check_stalled()
    assert not [x for x in sent if x["discord"] == "https://OWNSTL2"]


def test_deep_health_logic(app_mods):
    r = app_mods.R.Runner()
    ok, info = r.deep_health()
    assert ok and info["db"] and info["status"] == "ok"
    r.scheduler_on = True
    r.last_tick = time.time() - 300
    ok, info = r.deep_health()
    assert not ok and info["status"] == "fail" and info["scheduler_age"] > 120
    r.last_tick = time.time()
    t = threading.Thread(target=lambda: None, name="bara-worker-0")
    t.start(); t.join()
    r._threads.append(t)  # worker yang sudah mati
    ok, info = r.deep_health()
    assert not ok and info["workers"] == {"total": 1, "alive": 0}


def test_deep_health_endpoint(make_server):
    srv = make_server("legacy")
    assert requests.get(srv.base + "/api/health").json() == {"status": "ok"}
    r = requests.get(srv.base + "/api/health?deep=1")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok" and j["db"] is True and j["workers"]["alive"] == j["workers"]["total"] >= 1 and j["scheduler_age"] < 120


def test_dead_mans_switch_ping(app_mods, monkeypatch):
    hits = []

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        def log_message(self, *a): pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    cfg = app_mods.R.config
    monkeypatch.setattr(cfg, "HEALTHCHECK_PING_URL", f"http://127.0.0.1:{srv.server_address[1]}/ping/abc")
    r = app_mods.R.Runner()
    assert r.ping() is True and hits == ["/ping/abc"]
    r.scheduler_on = True
    r.last_tick = time.time() - 600  # scheduler macet -> tidak ping
    assert r.ping() is False and hits == ["/ping/abc"]
    monkeypatch.setattr(cfg, "HEALTHCHECK_PING_URL", "")
    r.last_tick = time.time()
    assert r.ping() is False
    srv.shutdown()
