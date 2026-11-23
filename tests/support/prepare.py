"""Menyiapkan state lewat API pada server yang sedang jalan. Pakai: prepare.py BASE PROFILE

PROFILE: setup  = admin pertama (admin / password1)
         seeded = setup + pengguna budi, jadwal, kontak, dan cookie palsu
"""
import sys

import requests

B = sys.argv[1]
PROFILE = sys.argv[2] if len(sys.argv) > 2 else "setup"
H = {"X-Requested-With": "bara"}
s = requests.Session()
r = s.post(B + "/api/auth/setup", json={"api_key": "testkey123", "username": "admin", "password": "password1"}, headers=H)
assert r.status_code == 200, r.text
if PROFILE == "seeded":
    s.post(B + "/api/users", json={"username": "budi", "password": "budipass1", "role": "user"}, headers=H)
    s.put(B + "/api/accounts/main", headers=H, json={"name": "Utama", "schedules": [
        {"time": "07:00", "enabled": True, "message": ""}, {"time": "19:30", "enabled": True, "message": "Malam", "contacts": ["Rina"]}]})
    s.post(B + "/api/contacts?account=main", json={"names": "Dimas\nSari Putri"}, headers=H)
    s.put(B + "/api/cookies?account=main", json={"raw": "sessionid=abc; tt_csrf=1"}, headers=H)
    s.put(B + "/api/cookies?account=second", json={"raw": "foo=bar"}, headers=H)
