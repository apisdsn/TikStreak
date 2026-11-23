"""Mengisi dua job antre (kirim dan cek untuk akun 'main') yang belum jatuh tempo."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app import db, jobs  # noqa: E402

adm = db.q1("SELECT id FROM users ORDER BY id LIMIT 1")["id"]
db.x("DELETE FROM jobs")
jobs.enqueue("main", adm, "send", "schedule", label="07:00", due_at=time.time() + 1800)
jobs.enqueue("main", adm, "check", "schedule", due_at=time.time() + 3600)
