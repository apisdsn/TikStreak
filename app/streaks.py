"""Perhitungan streak per kontak (murni, tanpa database) dipakai migrasi dan pembaruan setelah tiap run."""
from datetime import date, timedelta

EMPTY = {"last_ok_at": None, "last_fail_at": None, "last_error": None, "streak_days": 0, "streak_date": None}
SKIP_STATUS = ("running", "expired", "cancelled")


def stamp(run, result):
    """Waktu (ISO) sebuah hasil kirim: tanggal mulai run + jam kirim bila ada."""
    day = (run.get("started_at") or "")[:10]
    t = result.get("sent_at")
    if day and t and len(t) >= 5:
        return f"{day}T{t if len(t) >= 8 else t + ':00'}"
    return run.get("finished_at") or run.get("started_at")


def advance(state, ok, at, error=None):
    """Kembalikan state baru setelah satu hasil kirim. Streak = hari beruntun dengan >= 1 kiriman sukses."""
    s = {**EMPTY, **(state or {})}
    if not at:
        return s
    day = at[:10]
    if ok:
        s["last_ok_at"] = at
        if s["streak_date"] != day:
            prev = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
            s["streak_days"] = (s["streak_days"] or 0) + 1 if s["streak_date"] == prev else 1
            s["streak_date"] = day
    else:
        s["last_fail_at"] = at
        s["last_error"] = error
    return s


def effective_streak(state, today):
    """Streak yang masih hidup pada hari `today` (ISO): reset ke 0 bila kemarin terlewat."""
    if not state or not state.get("streak_date"):
        return 0
    yesterday = (date.fromisoformat(today) - timedelta(days=1)).isoformat()
    return state["streak_days"] if state["streak_date"] >= yesterday else 0
