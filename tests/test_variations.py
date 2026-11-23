import json
import os
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime, timedelta
from threading import Event

import pytest

from conftest import ROOT

SETTINGS = {"message": "Pesan Default"}


def acc(**kw):
    return {"id": "acc1", "variations": [], "random_emoji": False, **kw}


def test_resolution_order_and_fallback():
    from app import messages as M
    today = "2026-11-20"
    assert M.resolve(SETTINGS, acc(), "Rina", None, today) == "Pesan Default"                      # tanpa variasi: default
    a = acc(variations=["V1", "V2", "V3"])
    assert M.resolve(SETTINGS, a, "Rina", "Pesan Jadwal", today) == "Pesan Jadwal"                  # pesan jadwal menimpa
    assert M.resolve(SETTINGS, a, "Rina", "   ", today) in ("V1", "V2", "V3")                       # kosong = tidak menimpa
    assert M.resolve(SETTINGS, acc(variations=["", "  "]), "Rina", None, today) == "Pesan Default"  # variasi kosong diabaikan


def test_deterministic_per_contact_and_day():
    from app import messages as M
    a = acc(variations=[f"V{i}" for i in range(10)])
    for name in ("Rina", "Dimas"):
        assert M.resolve(SETTINGS, a, name, None, "2026-11-20") == M.resolve(SETTINGS, a, name, None, "2026-11-20")  # percobaan ulang = teks sama
    picks = {M.resolve(SETTINGS, a, "Rina", None, (datetime(2026, 11, 1) + timedelta(days=i)).strftime("%Y-%m-%d")) for i in range(60)}
    assert len(picks) >= 8  # variasi benar-benar berganti dari hari ke hari
    assert len({M.resolve(SETTINGS, a, f"Kontak{i}", None, "2026-11-20") for i in range(60)}) >= 8  # dan antar kontak
    assert M.resolve(SETTINGS, a, " rina ", None, "2026-11-20") == M.resolve(SETTINGS, a, "Rina", None, "2026-11-20")  # huruf besar/spasi tidak mengubah pilihan


def test_placeholders_and_day_number():
    from app import messages as M
    a = acc(variations=["Halo {nama}, hari ke-{hari}!"])
    today = "2026-11-20"
    assert M.resolve(SETTINGS, a, "Rina", None, today) == "Halo Rina, hari ke-1!"                    # kontak baru
    st = {"streak_days": 7, "streak_date": "2026-11-19"}
    assert M.resolve(SETTINGS, a, "Rina", None, today, st) == "Halo Rina, hari ke-8!"                # streak + 1
    st_today = {"streak_days": 8, "streak_date": today}
    assert M.resolve(SETTINGS, a, "Rina", None, today, st_today) == "Halo Rina, hari ke-8!"          # sudah terkirim hari ini: angka tetap (stabil)
    assert M.resolve(SETTINGS, a, "Rina", None, today, {"streak_days": 7, "streak_date": "2026-11-10"}) == "Halo Rina, hari ke-1!"  # streak putus
    assert M.resolve(SETTINGS, acc(), "Rina", "Hai {nama} {hari}", today, st) == "Hai Rina 8"         # placeholder juga di pesan jadwal


def test_random_emoji_from_set_and_stable():
    from app import messages as M
    a = acc(random_emoji=True)
    seen = set()
    for i in range(40):
        out = M.resolve(SETTINGS, a, f"K{i}", None, "2026-11-20")
        base, _, emo = out.rpartition(" ")
        assert base == "Pesan Default" and emo in M.EMOJIS
        seen.add(emo)
        assert out == M.resolve(SETTINGS, a, f"K{i}", None, "2026-11-20")  # stabil untuk percobaan ulang
    assert len(seen) >= 3
    assert M.resolve(SETTINGS, acc(random_emoji=False), "K", None, "2026-11-20") == "Pesan Default"


def test_bot_uses_message_per_contact():
    from app.bot import StreakBot
    sent = []

    class Fake(StreakBot):
        def _create_browser(self): pass
        def _load_cookies(self): pass
        def _verify_login(self): pass
        def _sleep(self, s): pass
        def _capture_proof(self, i): return None
        def _send_to(self, name):
            sent.append((name, self.message))
            return {}

    texts = {"Rina": "untuk Rina", "Dimas": "untuk Dimas"}
    bot = Fake({"message": "x", "element_wait": 0, "page_load_wait": 0, "notify_screenshot": False}, lambda *a, **k: None, Event(), None, message_fn=lambda n: texts[n])
    res = bot.run(["Rina", "Dimas"])
    assert sent == [("Rina", "untuk Rina"), ("Dimas", "untuk Dimas")]
    assert [r["message"] for r in res["results"]] == ["untuk Rina", "untuk Dimas"]


def test_runner_message_fn_uses_stats_and_account(app_mods):
    m = app_mods
    u = m.auth.make_user("varown1", "password1", "user")
    m.store.user_save(u)
    m.store.save_account({"id": "vr01", "name": "V", "owner_id": u["id"], "schedules": [], "variations": ["Hari {hari} untuk {nama}"], "random_emoji": False})
    yday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    m.db.x("INSERT INTO contact_stats(account_id, name_lc, last_ok_at, streak_days, streak_date) VALUES('vr01','rina',?,4,?)", (yday + "T07:00:00", yday))
    fn = m.R.Runner()._message_fn({"account": {"id": "vr01"}, "message": None}, {"message": "default", "timezone": ""})
    assert fn("Rina") == "Hari 5 untuk Rina" and fn("Baru") == "Hari 1 untuk Baru"


def test_account_api_variations(user, client):
    c, _ = user("varapi")
    aid = c.get("/api/status").json()["accounts"][0]["id"]
    a = c.get("/api/status").json()["accounts"][0]
    assert a["variations"] == [] and a["random_emoji"] is False
    r = c.put(f"/api/accounts/{aid}", json={"variations": ["  Satu {nama} ", "", "Dua"], "random_emoji": True})
    assert r.status_code == 200 and r.json()["variations"] == ["Satu {nama}", "Dua"] and r.json()["random_emoji"] is True
    # menyimpan jadwal tidak menghapus variasi
    r = c.put(f"/api/accounts/{aid}", json={"schedules": [{"time": "07:00", "enabled": True, "message": ""}]})
    assert r.json()["variations"] == ["Satu {nama}", "Dua"] and r.json()["random_emoji"] is True
    assert c.put(f"/api/accounts/{aid}", json={"variations": [f"v{i}" for i in range(21)]}).status_code == 400
    assert c.put(f"/api/accounts/{aid}", json={"variations": ["x" * 501]}).status_code == 400
    assert c.put(f"/api/accounts/{aid}", json={"variations": [f"v{i}" for i in range(20)]}).status_code == 200
    r = c.put(f"/api/accounts/{aid}", json={"variations": [], "random_emoji": False})
    assert r.json()["variations"] == [] and r.json()["random_emoji"] is False


def test_migration_6_keeps_accounts_and_messages():
    tmp = tempfile.mkdtemp(prefix="bara-mig6-")
    code = textwrap.dedent(f"""
        import json, sys
        sys.path.insert(0, {ROOT!r})
        from app import db
        full = list(db.MIGRATIONS)
        db.MIGRATIONS = full[:5]
        db.init()
        c = db.conn()
        c.execute("INSERT INTO accounts(id, name) VALUES('a1','Lama')")
        c.execute("INSERT INTO schedules(id, account_id, time, enabled, message, position) VALUES('s1','a1','07:00',1,'Pesan Lama',0)")
        c.execute("INSERT INTO settings(key, value_json) VALUES('message', '\\"Default Lama\\"')")
        c.commit()
        db.MIGRATIONS = full
        db._ready.clear()
        db.init()
        from app import store
        a = store.get_account('a1')
        print(json.dumps([a['name'], a['schedules'][0]['message'], a['variations'], a['random_emoji'], store.get_settings()['message'], db.q1("PRAGMA user_version")[0]]))
    """)
    p = subprocess.run([sys.executable, "-c", code], env={**os.environ, "DATA_DIR": tmp, "API_KEY": "k"}, capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr[-1200:]
    assert json.loads(p.stdout.strip().splitlines()[-1]) [:5] == ["Lama", "Pesan Lama", [], False, "Default Lama"]
