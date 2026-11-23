"""Data awal untuk tes: folder data format JSON lama (dua akun, dua kontak, dua riwayat)."""
import base64
import json
import os
import sys

# JPEG 1x1 valid, cukup untuk bukti kirim dan screenshot palsu
JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
    "wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
)


def _run(i, acc, name, contact):
    return {"id": i, "account": {"id": acc, "name": name}, "mode": "send", "trigger": "manual", "label": None, "status": "success",
            "started_at": "2026-11-16T07:00:05", "finished_at": "2026-11-16T07:00:50", "sent": 1, "total": 1, "error": None,
            "results": [{"contact": contact, "ok": True, "proof": "1.jpg", "sent_at": "07:00:12", "evidence": {}}], "logs": []}


def legacy(d):
    os.makedirs(d + "/accounts/main", exist_ok=True)
    os.makedirs(d + "/accounts/second", exist_ok=True)
    json.dump([{"id": "main", "name": "Utama", "schedules": []}, {"id": "second", "name": "Kedua", "schedules": []}], open(d + "/accounts.json", "w"))
    json.dump(["Rina"], open(d + "/accounts/main/contacts.json", "w"))
    json.dump(["Budi"], open(d + "/accounts/second/contacts.json", "w"))
    json.dump({"keepalive_enabled": False}, open(d + "/settings.json", "w"))
    json.dump([_run("aaaaaaaa", "main", "Utama", "Rina"), _run("bbbbbbbb", "second", "Kedua", "Budi")], open(d + "/history.json", "w"))
    for rid in ("aaaaaaaa", "bbbbbbbb"):
        os.makedirs(f"{d}/proofs/{rid}", exist_ok=True)
        open(f"{d}/proofs/{rid}/1.jpg", "wb").write(JPEG)
    open(d + "/last_run.jpg", "wb").write(JPEG)
    json.dump({"account_id": "second"}, open(d + "/last_run.json", "w"))


if __name__ == "__main__":
    legacy(sys.argv[1])
