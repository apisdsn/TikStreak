import time
from datetime import datetime

import pytest

GOOD_SETTINGS = {"retry_enabled": True, "retry_delay_min": 30, "retry_max": 2, "message": "x"}


def mk(m, name, aid, contacts=("Rina", "Dimas", "Sari")):
    u = m.auth.make_user(name, "password1", "user")
    m.store.user_save(u)
    m.store.save_account({"id": aid, "name": aid, "owner_id": u["id"], "schedules": []})
    m.store.stores(aid).contacts.write(list(contacts))
    return u


def sched_run(aid, owner, results, status="partial", trigger="schedule", attempt=0, **kw):
    return {"id": "rt" + aid[-4:], "account": {"id": aid, "name": aid}, "owner_id": owner["id"], "mode": "send", "trigger": trigger, "label": "07:00" if trigger == "schedule" else "Ulang",
            "status": status, "started_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "finished_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "sent": sum(1 for r in results if r["ok"]), "total": len(results), "results": results, "logs": [], "attempt": attempt, "message": "Halo", **kw}


TRANSIENT_ERR = "Pesan Tidak Terverifikasi Terkirim (Cek Screenshot)"


def test_error_classification(app_mods):
    f = app_mods.R.Runner.is_transient
    for e in (TRANSIENT_ERR, "Timeout menunggu halaman", "页面连接已断开", "Browser crash: Target closed", "Gagal memuat halaman pesan", "Connection reset"):
        assert f(e), e
    for e in ("Kontak Tidak Ditemukan di Daftar Pesan", "Cookie sessionid Ditolak TikTok", "Kolom Pesan Tidak Ditemukan", "Chat yang Terbuka Milik 'X', Bukan 'Y'", "Browser Tidak Ditemukan di /x", "", None):
        assert not f(e), e


def pending_retry(m, aid):
    return [j for j in m.jobs.queued() if j["account_id"] == aid and j["trigger"] == "retry"]


def test_retry_enqueued_for_transient_failures_only(app_mods):
    m = app_mods
    u = mk(m, "retr1", "rt01")
    r = m.R.Runner()
    run = sched_run("rt01", u, [{"contact": "Rina", "ok": True}, {"contact": "Dimas", "ok": False, "error": TRANSIENT_ERR}, {"contact": "Sari", "ok": False, "error": "Kontak Tidak Ditemukan di Daftar Pesan"}])
    t0 = time.time()
    r._maybe_retry({**GOOD_SETTINGS, "timezone": "UTC"}, run)
    jobs = pending_retry(m, "rt01")
    assert len(jobs) == 1
    j = jobs[0]
    assert j["contacts"] == ["Dimas"] and j["label"] == "Ulang" and j["attempt"] == 1 and j["kind"] == "send" and j["message"] == "Halo"
    assert 29 * 60 <= j["due_at"] - t0 <= 31 * 60  # RETRY_DELAY_MIN
    assert j["priority"] == 1  # prioritas terjadwal, bukan manual


def test_retry_respects_attempt_limit_toggle_trigger_and_cookie(app_mods):
    m = app_mods
    u = mk(m, "retr2", "rt02")
    r = m.R.Runner()
    bad = [{"contact": "Dimas", "ok": False, "error": TRANSIENT_ERR}]
    r._maybe_retry(GOOD_SETTINGS, sched_run("rt02", u, bad, "failed", trigger="retry", attempt=2))      # batas tercapai
    r._maybe_retry({**GOOD_SETTINGS, "retry_enabled": False}, sched_run("rt02", u, bad, "failed"))      # dimatikan
    r._maybe_retry(GOOD_SETTINGS, sched_run("rt02", u, bad, "failed", trigger="manual"))               # manual tidak diulang
    r._maybe_retry(GOOD_SETTINGS, sched_run("rt02", u, bad, "failed", cookie_invalid=True))             # cookie bermasalah
    r._maybe_retry(GOOD_SETTINGS, sched_run("rt02", u, [{"contact": "A", "ok": True}], "success"))
    assert pending_retry(m, "rt02") == []
    r._maybe_retry(GOOD_SETTINGS, sched_run("rt02", u, bad, "failed", trigger="retry", attempt=1))     # percobaan kedua masih boleh
    assert [j["attempt"] for j in pending_retry(m, "rt02")] == [2]


def test_retry_whole_run_failure_and_duplicates_and_cutoff(app_mods, monkeypatch):
    m = app_mods
    u = mk(m, "retr3", "rt03")
    r = m.R.Runner()
    crash = sched_run("rt03", u, [], "failed", error="Browser crash: Target closed", only=["Rina"])
    r._maybe_retry(GOOD_SETTINGS, crash)
    assert pending_retry(m, "rt03")[0]["contacts"] == ["Rina"]  # run gagal total: ulangi kontak yang dipilih jadwal
    r._maybe_retry(GOOD_SETTINGS, crash)  # sudah ada job kirim akun ini di antrean: dilewati tanpa error
    assert len(pending_retry(m, "rt03")) == 1
    # perkiraan mulai setelah batas 23:50 -> dibatalkan
    u4 = mk(m, "retr4", "rt04")
    monkeypatch.setattr(m.R, "RETRY_CUTOFF", "00:00")
    r._maybe_retry(GOOD_SETTINGS, sched_run("rt04", u4, [{"contact": "Dimas", "ok": False, "error": TRANSIENT_ERR}], "failed"))
    assert pending_retry(m, "rt04") == []


def test_retry_notification_and_label(app_mods, sent):
    m = app_mods
    u = mk(m, "retr5", "rt05")
    u["notify"] = {"discord_enabled": True, "discord_webhook": "https://RT5"}
    m.store.user_save(u)
    run = sched_run("rt05", u, [{"contact": "Dimas", "ok": True, "sent_at": "07:31:00"}], "success", trigger="retry", attempt=1)
    run["mode"] = "send"
    m.R.Runner()._notify({**GOOD_SETTINGS, "message": "x"}, run)
    mine = [x for x in sent if x["discord"] == "https://RT5"]
    assert mine and "Percobaan Ulang" in mine[0]["title"] and mine[0]["lines"][0].startswith("Percobaan Ulang ke-1 dari 2")
    assert not any("Jadwal" in l for l in mine[0]["lines"][:1])


def test_retry_updates_contact_stats(app_mods):
    m = app_mods
    u = mk(m, "retr6", "rt06")
    day = datetime.now().strftime("%Y-%m-%d")
    first = sched_run("rt06", u, [{"contact": "Dimas", "ok": False, "error": TRANSIENT_ERR}], "failed")
    m.store.contact_stats_apply(first)
    assert m.store.contact_stats("rt06")["dimas"]["last_ok_at"] is None
    retry = sched_run("rt06", u, [{"contact": "Dimas", "ok": True, "sent_at": "07:40:00"}], "success", trigger="retry", attempt=1)
    retry["id"] = "rt06retry"
    m.store.contact_stats_apply(retry)
    s = m.store.contact_stats("rt06")["dimas"]
    assert s["last_ok_at"] == f"{day}T07:40:00" and s["streak_days"] == 1


def test_settings_api_for_retry(user, client):
    c, _ = user("retadm", role="admin")
    s = c.get("/api/settings").json()
    assert s["retry_enabled"] is True and s["retry_delay_min"] == 30 and s["retry_max"] == 2
    r = c.put("/api/settings", json={"retry_enabled": False, "retry_delay_min": 45, "retry_max": 3})
    assert r.status_code == 200 and (r.json()["retry_enabled"], r.json()["retry_delay_min"], r.json()["retry_max"]) == (False, 45, 3)
    assert c.put("/api/settings", json={"retry_delay_min": 0}).status_code == 400
    assert c.put("/api/settings", json={"retry_max": 9}).status_code == 400
    c.put("/api/settings", json={"retry_enabled": True, "retry_delay_min": 30, "retry_max": 2})


def test_jobs_have_attempt_column_from_migration(app_mods):
    cols = [r["name"] for r in app_mods.db.q("PRAGMA table_info(jobs)")]
    assert "attempt" in cols


def test_migration_5_keeps_existing_jobs():
    import json, os, subprocess, sys, tempfile, textwrap
    from conftest import ROOT
    tmp = tempfile.mkdtemp(prefix="bara-mig5-")
    code = textwrap.dedent(f"""
        import json, sys, time
        sys.path.insert(0, {ROOT!r})
        from app import db
        full = list(db.MIGRATIONS)
        db.MIGRATIONS = full[:4]
        db.init()
        c = db.conn()
        c.execute("INSERT INTO accounts(id, name) VALUES('a1','A')")
        c.execute("INSERT INTO jobs(id, account_id, kind, trigger, priority, due_at, enqueued_at, status) VALUES('j1','a1','send','schedule',1,?,?, 'queued')", (time.time(), time.time()))
        c.commit()
        db.MIGRATIONS = full
        db._ready.clear()
        db.init()
        print(json.dumps([dict(db.q1("SELECT id, attempt FROM jobs WHERE id='j1'")), db.q1("PRAGMA user_version")[0]]))
    """)
    p = subprocess.run([sys.executable, "-c", code], env={**os.environ, "DATA_DIR": tmp, "API_KEY": "k"}, capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr[-1200:]
    row, ver = json.loads(p.stdout.strip().splitlines()[-1])
    assert row == {"id": "j1", "attempt": 0} and ver == 5
