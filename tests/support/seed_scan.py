"""Mengisi hasil pindai kontak palsu untuk akun 'main' (menggantikan browser TikTok)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app import store  # noqa: E402

names = ["Rina", "Dimas", "Sari Putri", "Budi Santoso", "Ayu Lestari", "Fajar", "Maya", "Joko", "Tia", "Wawan"]
store.scan_set("main", [{"id": f"conv{i}", "nick": n, "time": f"{8 + i % 10:02d}:{(i * 7) % 60:02d}"} for i, n in enumerate(names)])
