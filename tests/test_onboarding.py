import json
import os
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime

from conftest import ROOT


def state(c, aid):
    return c.get(f"/api/dashboard?account={aid}").json()["onboarding"]


def done_keys(o):
    return [s["key"] for s in o["steps"] if s["done"]]


def test_steps_follow_account_state(user, client, app_mods):
    m = app_mods
    c, u = user("onb1")
    aid = c.get("/api/status").json()["accounts"][0]["id"]
    o = state(c, aid)
    assert o["total"] == 5 and o["done"] == 0 and o["visible"] and [s["key"] for s in o["steps"]] == ["cookie", "contacts", "schedule", "notify", "test"]
    m.store.stores(aid).cookies.write([{"name": "sessionid", "value": "x", "domain": ".tiktok.com"}])
    assert done_keys(state(c, aid)) == ["cookie"]
    meta = m.store.stores(aid).meta.read()
    m.store.stores(aid).meta.write({**meta, "invalid": "Cookie Kedaluwarsa"})
    assert done_keys(state(c, aid)) == []  # cookie tidak valid belum dianggap terhubung
    m.store.stores(aid).meta.write({k: v for k, v in meta.items() if k != "invalid"})
    m.store.stores(aid).contacts.write(["Rina"])
    acc = m.store.get_account(aid)
    acc["schedules"] = [{"id": "sx", "enabled": False, "time": "07:00", "message": "", "contacts": None}]
    m.store.save_account(acc)
    assert done_keys(state(c, aid)) == ["cookie", "contacts"]  # jadwal nonaktif belum dihitung
    acc["schedules"][0]["enabled"] = True
    m.store.save_account(acc)
    assert done_keys(state(c, aid)) == ["cookie", "contacts", "schedule"]
    u2 = m.auth.get_user(u["id"])
    u2["notify"] = {"discord_enabled": True, "discord_webhook": "https://discord.com/api/webhooks/1/x"}
    m.store.user_save(u2)
    assert done_keys(state(c, aid)) == ["cookie", "contacts", "schedule", "notify"]
    run = {"id": "onbtest1", "account": {"id": aid, "name": "a"}, "owner_id": u["id"], "mode": "test", "trigger": "manual", "status": "failed", "started_at": "2026-11-20T07:00:00",
           "finished_at": "2026-11-20T07:00:30", "sent": 0, "total": 1, "results": [], "logs": []}
    m.store.insert_run(run)
    assert "test" not in done_keys(state(c, aid))  # uji yang gagal tidak dihitung
    m.store.insert_run({**run, "id": "onbtest2", "status": "success"})
    o = state(c, aid)
    assert o["done"] == 5 and o["visible"] is False  # semua selesai: kartu hilang sendiri


def test_dismissal_is_stored_per_user_and_account(user, client, app_mods):
    m = app_mods
    c, u = user("onb2")
    other, _ = user("onb3")
    aid = c.get("/api/status").json()["accounts"][0]["id"]
    oaid = other.get("/api/status").json()["accounts"][0]["id"]
    second = m.store.create_account("Kedua", u["id"])
    assert state(c, aid)["visible"] and state(c, second["id"])["visible"]
    r = c.post(f"/api/onboarding/dismiss?account={aid}")
    assert r.status_code == 200 and r.json()["visible"] is False and r.json()["dismissed"] is True
    assert state(c, aid)["visible"] is False
    assert state(c, second["id"])["visible"] is True            # akun lain milik pengguna yang sama tetap tampil
    assert state(other, oaid)["visible"] is True                # pengguna lain tidak terpengaruh
    assert c.post(f"/api/onboarding/dismiss?account={aid}").status_code == 200  # idempoten
    assert other.post(f"/api/onboarding/dismiss?account={aid}").status_code == 404  # bukan akunnya
    row = m.db.q1("SELECT * FROM onboarding_dismissed WHERE user_id=? AND account_id=?", (u["id"], aid))
    assert row and row["dismissed_at"]


def test_migration_7():
    tmp = tempfile.mkdtemp(prefix="bara-mig7-")
    code = textwrap.dedent(f"""
        import json, sys
        sys.path.insert(0, {ROOT!r})
        from app import db
        full = list(db.MIGRATIONS)
        db.MIGRATIONS = full[:6]
        db.init()
        c = db.conn()
        c.execute("INSERT INTO accounts(id, name) VALUES('a1','A')")
        c.commit()
        db.MIGRATIONS = full
        db._ready.clear()
        db.init()
        print(json.dumps([db.q1("PRAGMA user_version")[0], db.q1("SELECT COUNT(*) FROM onboarding_dismissed")[0], db.q1("SELECT name FROM accounts")[0]]))
    """)
    p = subprocess.run([sys.executable, "-c", code], env={**os.environ, "DATA_DIR": tmp, "API_KEY": "k"}, capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr[-1200:]
    assert json.loads(p.stdout.strip().splitlines()[-1]) == [7, 0, "A"]
