"""Satu run percobaan ulang (trigger retry, label Ulang) untuk akun 'main', agar tampil di riwayat."""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app import db, store  # noqa: E402

adm = db.q1("SELECT id FROM users WHERE role='admin' ORDER BY created_at LIMIT 1")["id"]
d = datetime.now().strftime("%Y-%m-%d")
store.insert_run({"id": store.new_run_id(), "account": {"id": "main", "name": "Utama"}, "owner_id": adm, "mode": "send", "trigger": "retry", "label": "Ulang", "by": "system",
                  "status": "success", "started_at": d + "T07:31:00", "finished_at": d + "T07:31:40", "sent": 1, "total": 1,
                  "results": [{"contact": "Dimas", "ok": True, "sent_at": "07:31:20"}], "logs": []})
