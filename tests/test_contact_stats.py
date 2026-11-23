import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
from datetime import datetime, timedelta

import pytest

from conftest import ROOT


def test_streak_logic():
    from app import streaks as s
    st = None
    for day, ok in (("2026-11-10", True), ("2026-11-10", True), ("2026-11-11", True), ("2026-11-12", False), ("2026-11-12", True)):
        st = s.advance(st, ok, day + "T07:00:00", None if ok else "err")
    assert st["streak_days"] == 3 and st["streak_date"] == "2026-11-12" and st["last_fail_at"].startswith("2026-11-12")
    assert s.effective_streak(st, "2026-11-12") == 3 and s.effective_streak(st, "2026-11-13") == 3  # kemarin masih ada kiriman
    assert s.effective_streak(st, "2026-11-14") == 0  # satu hari terlewat: reset
    st = s.advance(st, True, "2026-11-15T07:00:00")  # setelah celah, mulai lagi dari 1
    assert st["streak_days"] == 1
    assert s.effective_streak(None, "2026-11-12") == 0


def _run(aid, day, results, status="success", mode="send"):
    return {"id": f"{aid[:4]}{day[-2:]}{abs(hash(str(results))) % 9999:04d}", "account": {"id": aid, "name": aid}, "mode": mode, "trigger": "manual", "status": status,
            "started_at": day + "T07:00:00", "finished_at": day + "T07:01:00", "sent": sum(1 for r in results if r["ok"]), "total": len(results), "results": results, "logs": []}


def mk(m, name, aid, contacts, schedules=None):
    u = m.auth.make_user(name, "password1", "user")
    m.store.user_save(u)
    m.store.save_account({"id": aid, "name": aid, "owner_id": u["id"], "schedules": schedules or []})
    m.store.stores(aid).contacts.write(contacts)
    return u


def test_apply_after_runs_and_rename(app_mods):
    m = app_mods
    mk(m, "cstat1", "cs1", ["Rina", "Dimas"])
    ok = lambda n: {"contact": n, "ok": True, "sent_at": "07:00:30"}
    bad = lambda n: {"contact": n, "ok": False, "error": "Pesan Tidak Terverifikasi Terkirim"}
    m.store.contact_stats_apply(_run("cs1", "2026-11-10", [ok("Rina"), bad("Dimas")], "partial"))
    m.store.contact_stats_apply(_run("cs1", "2026-11-11", [ok("Rina"), ok("Dimas")]))
    m.store.contact_stats_apply(_run("cs1", "2026-11-12", [ok("Rina")], "success", mode="test"))  # uji tidak dihitung
    m.store.contact_stats_apply(_run("cs1", "2026-11-12", [ok("Rina")], "cancelled"))             # dihentikan tidak dihitung
    s = m.store.contact_stats("cs1")
    assert s["rina"]["streak_days"] == 2 and s["rina"]["streak_date"] == "2026-11-11"
    assert s["dimas"]["streak_days"] == 1 and s["dimas"]["last_error"].startswith("Pesan Tidak") and s["dimas"]["last_fail_at"].startswith("2026-11-10")
    m.store.rename_contact("cs1", "Rina", "Rina S")
    s = m.store.contact_stats("cs1")
    assert "rina" not in s and s["rina s"]["streak_days"] == 2  # status ikut berganti nama


def test_migration_backfills_from_existing_runs():
    tmp = tempfile.mkdtemp(prefix="bara-mig4-")
    code = textwrap.dedent(f"""
        import json, os, sys
        sys.path.insert(0, {ROOT!r})
        from app import db
        full = list(db.MIGRATIONS)
        db.MIGRATIONS = full[:3]                   # state sebelum migrasi 4
        db.init()
        c = db.conn()
        c.execute("INSERT INTO accounts(id, name) VALUES('a1','A')")
        def run(i, day, results, status='success', mode='send'):
            c.execute("INSERT INTO runs(id, account_id, mode, trigger, status, started_at, finished_at, sent, total, results_json) VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (i, 'a1', mode, 'manual', status, day + 'T07:00:00', day + 'T07:01:00', 1, 1, json.dumps(results)))
        ok = {{'contact': 'Rina', 'ok': True, 'sent_at': '07:00:10'}}
        run('r1', '2026-11-10', [ok]); run('r2', '2026-11-11', [ok]); run('r3', '2026-11-12', [dict(ok, ok=False, error='x')], 'failed')
        run('r4', '2026-11-13', [ok], mode='test'); run('r5', '2026-11-13', [ok], status='expired')
        c.commit()
        db.MIGRATIONS = full
        db._ready.clear()
        db.init()
        row = dict(db.q1("SELECT * FROM contact_stats WHERE account_id='a1' AND name_lc='rina'"))
        print(json.dumps([row, db.q1("PRAGMA user_version")[0]]))
    """)
    p = subprocess.run([sys.executable, "-c", code], env={**os.environ, "DATA_DIR": tmp, "API_KEY": "k"}, capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr[-1500:]
    row, ver = json.loads(p.stdout.strip().splitlines()[-1])
    assert ver >= 4 and row["streak_days"] == 2 and row["streak_date"] == "2026-11-11"
    assert row["last_ok_at"] == "2026-11-11T07:00:10" and row["last_fail_at"].startswith("2026-11-12") and row["last_error"] == "x"


def test_status_endpoint_dashboard_and_single_contact_resend(client, user, app_mods):
    c, u = user("cstat2")
    aid = c.get("/api/status").json()["accounts"][0]["id"]
    st = app_mods.store.stores(aid)
    st.contacts.write(["Sent", "Failed", "Waiting", "Lonely"])
    acc = app_mods.store.get_account(aid)
    acc["schedules"] = [{"id": "sx", "enabled": True, "time": "07:00", "message": "", "contacts": ["Sent", "Failed", "Waiting"]}]
    app_mods.store.save_account(acc)
    today = datetime.now().strftime("%Y-%m-%d")
    run = _run(aid, today, [{"contact": "Sent", "ok": True, "sent_at": "07:00:10"}, {"contact": "Failed", "ok": False, "error": "Kolom Pesan Tidak Ditemukan"}], "partial")
    app_mods.store.contact_stats_apply(run)
    rows = {r["name"]: r for r in c.get(f"/api/contacts/status?account={aid}").json()["contacts"]}
    assert rows["Sent"]["today"] == "sent" and rows["Sent"]["streak"] == 1
    assert rows["Failed"]["today"] == "failed" and rows["Failed"]["last_error"] == "Kolom Pesan Tidak Ditemukan"
    assert rows["Waiting"]["today"] == "pending" and rows["Lonely"]["today"] == "unscheduled"
    d = c.get(f"/api/dashboard?account={aid}").json()
    assert d["needs_check"] == [{"name": "Failed", "error": "Kolom Pesan Tidak Ditemukan"}]
    # kirim ulang satu kontak
    seen = []
    def fake(run, job, cancel, prov):
        seen.append(run.get("only"))
        run.update(status="success", sent=1, total=1, results=[{"contact": "Failed", "ok": True, "sent_at": "09:00:00"}])
    old_exec = client.runner.executor
    client.runner.executor = fake
    try:
        r = c.post("/api/run", json={"mode": "send", "account": aid, "contacts": ["failed"]})
        assert r.status_code == 200
        t = time.time()
        while not seen and time.time() - t < 15:
            time.sleep(0.2)
        assert seen == [["Failed"]]  # hanya kontak itu, dengan penulisan nama dari daftar
        time.sleep(0.5)
        assert c.post("/api/run", json={"mode": "check", "account": aid, "contacts": ["Failed"]}).status_code == 400
        assert c.post("/api/run", json={"mode": "send", "account": aid, "contacts": ["Nobody"]}).status_code == 404
        # setelah kirim ulang sukses, kartu Perlu Dicek kosong
        t = time.time()
        while time.time() - t < 10 and c.get(f"/api/dashboard?account={aid}").json()["needs_check"]:
            time.sleep(0.2)
        assert c.get(f"/api/dashboard?account={aid}").json()["needs_check"] == []
    finally:
        client.runner.executor = old_exec
