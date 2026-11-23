"""Mengisi riwayat (134 run) untuk admin pertama pada DATA_DIR yang sedang dipakai server."""
import os
import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app import db, store  # noqa: E402

random.seed(3)
adm = db.q1("SELECT id FROM users ORDER BY id LIMIT 1")["id"]
have = db.q1("SELECT COUNT(*) n FROM runs WHERE owner_id=?", (adm,))["n"]
now = datetime(2026, 11, 16, 6, 0, 0)
for i in range(134 - have):
    aid, name = ("main", "Utama") if i % 2 == 0 else ("second", "Kedua")
    mode = "check" if i % 5 == 0 else "send"
    st = random.choice(["success", "success", "success", "partial", "failed", "expired"]) if mode == "send" else random.choice(["success", "failed"])
    t = now - timedelta(hours=3 * (i + 1))
    store.insert_run({"id": store.new_run_id(), "account": {"id": aid, "name": name}, "owner_id": adm, "mode": mode, "trigger": "manual", "by": "admin",
                      "label": None, "status": st, "started_at": t.isoformat(timespec="seconds"),
                      "finished_at": (t + timedelta(seconds=40)).isoformat(timespec="seconds"), "sent": 1 if st == "success" else 0, "total": 1,
                      "results": [], "logs": [{"t": "07:00:00", "level": "info", "msg": "x"}]})
