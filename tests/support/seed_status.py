"""Riwayat kirim 3 hari untuk akun 'main': Rina sukses 3 hari beruntun, Dimas gagal hari ini, Sari Putri belum dikirim."""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app import db, store  # noqa: E402

adm = db.q1("SELECT id FROM users WHERE role='admin' ORDER BY created_at LIMIT 1")["id"]
today = datetime.now()


def run(days_ago, results, status):
    d = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    r = {"id": store.new_run_id(), "account": {"id": "main", "name": "Utama"}, "owner_id": adm, "mode": "send", "trigger": "schedule", "label": "07:00",
         "status": status, "started_at": d + "T07:00:05", "finished_at": d + "T07:00:50", "sent": sum(1 for x in results if x["ok"]), "total": len(results),
         "results": results, "logs": []}
    store.insert_run(r)
    store.contact_stats_apply(r)


ok = lambda n: {"contact": n, "ok": True, "sent_at": "07:00:20", "evidence": {}}
run(2, [ok("Rina"), ok("Dimas")], "success")
run(1, [ok("Rina"), ok("Dimas")], "success")
run(0, [ok("Rina"), {"contact": "Dimas", "ok": False, "error": "Pesan Tidak Terverifikasi Terkirim (Cek Screenshot)"}], "partial")
