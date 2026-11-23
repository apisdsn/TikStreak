"""Menandai cookie akun 'main' tidak valid dengan teks lama (huruf kecil) dan membuat folder cadangan JSON palsu."""
import json
import os
import sqlite3

d = os.environ["DATA_DIR"]
c = sqlite3.connect(d + "/streak.db")
c.execute("update account_state set meta_json=? where account_id='main'", (json.dumps({"invalid": "Cookie TikTok belum diatur"}),))
c.commit()
os.makedirs(d + "/backup-json-20260101-000000", exist_ok=True)
