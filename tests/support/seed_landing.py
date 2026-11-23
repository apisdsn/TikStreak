"""Data palsu untuk tangkapan layar halaman depan: satu akun, empat kontak, jadwal 23:00, dua minggu kiriman."""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app import db, store  # noqa: E402

adm = db.q1("SELECT id FROM users WHERE role='admin' ORDER BY created_at LIMIT 1")["id"]
store.save_settings({**store.get_settings(), "message": "Streak hari ini"})
acc = store.get_account("main")
acc["name"] = "Utama"
acc["schedules"] = [{"id": "s23", "enabled": True, "time": "23:00", "message": "", "contacts": None}]
store.save_account(acc)
store.stores("main").contacts.write(["rina.s", "dimas_k", "sari.p", "budi_a"])
store.stores("main").cookies.write([{"name": "sessionid", "value": "x", "domain": ".tiktok.com"}])
store.stores("main").meta.write({"last_ok": datetime.now().isoformat(timespec="seconds")})
now = datetime.now()
for ago in range(1, 15):
    d = (now - timedelta(days=ago)).strftime("%Y-%m-%d")
    results = [{"contact": n, "ok": True, "sent_at": "23:0%d:10" % i, "evidence": {}} for i, n in enumerate(["rina.s", "dimas_k", "sari.p", "budi_a"])]
    run = {"id": store.new_run_id(), "account": {"id": "main", "name": "Utama"}, "owner_id": adm, "mode": "send", "trigger": "schedule", "label": "23:00",
           "status": "success", "started_at": d + "T23:00:05", "finished_at": d + "T23:04:10", "sent": 4, "total": 4, "results": results, "logs": []}
    store.insert_run(run)
    store.contact_stats_apply(run)
