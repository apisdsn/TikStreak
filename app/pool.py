"""Pool Chromium untuk job: satu proses per worker, konteks browser terisolasi per job."""
import glob
import logging
import os
import shutil
import tempfile
import threading
import time

from DrissionPage import ChromiumOptions, ChromiumPage

from . import browser, config

log = logging.getLogger("bara")
MEDIA_BLOCK = ["*.mp4", "*.m3u8", "*.webm", "*.mp3", "*.m4a", "*.m4s", "*.flv", "*mime_type=video*", "*mime_type=audio*"]
VIEW = (1366, 900)


def shell_path():
    """Lokasi chrome-headless-shell bila terpasang (lebih ringan dari Chromium penuh)."""
    if config.SHELL_PATH and os.path.exists(config.SHELL_PATH):
        return config.SHELL_PATH
    for pat in ("/usr/bin/chromium-headless-shell", "/usr/lib/chromium/headless_shell", "/usr/bin/chrome-headless-shell",
                "/opt/pw-browsers/chromium_headless_shell-*/*/chrome-headless-shell"):
        hit = sorted(glob.glob(pat))
        if hit:
            return hit[0]
    return ""


def job_binary():
    """(path, kind) browser untuk job send/check sesuai BROWSER_KIND."""
    kind = config.BROWSER_KIND
    sp = shell_path()
    if kind == "shell" and sp:
        return sp, "shell"
    if kind == "auto" and sp:
        return sp, "shell"
    return config.BROWSER_PATH, "full"


def tree_mem(root_pid):
    """Memori (MB) seluruh pohon proses dari root_pid: {'rss': jumlah RSS, 'pss': jumlah PSS}.

    RSS menghitung halaman bersama berulang kali; PSS membaginya adil antar proses sehingga lebih mendekati pemakaian nyata.
    """
    out = {"rss": 0.0, "pss": 0.0}
    try:
        page = os.sysconf("SC_PAGE_SIZE")
        kids, rss = {}, {}
        for d in os.listdir("/proc"):
            if not d.isdigit():
                continue
            try:
                with open(f"/proc/{d}/stat", "rb") as f:
                    raw = f.read().decode("utf-8", "replace")
                fields = raw[raw.rindex(")") + 2:].split()
                kids.setdefault(int(fields[1]), []).append(int(d))
                rss[int(d)] = int(fields[21]) * page
            except (OSError, ValueError, IndexError):
                continue
        stack, pids = [int(root_pid)], []
        while stack:
            p = stack.pop()
            pids.append(p)
            stack.extend(kids.get(p, []))
        pss = 0
        for p in pids:
            try:
                with open(f"/proc/{p}/smaps_rollup", "r") as f:
                    for line in f:
                        if line.startswith("Pss:"):
                            pss += int(line.split()[1]) * 1024
                            break
            except OSError:
                pss += rss.get(p, 0)
        out = {"rss": sum(rss.get(p, 0) for p in pids) / 1048576, "pss": pss / 1048576}
    except Exception:  # noqa: BLE001
        pass
    return out


class BrowserHolder:
    """Satu proses Chromium milik satu worker. acquire() memberi tab di konteks baru; release() membuangnya."""

    def __init__(self, idx=0, path=None, kind=None, use_new_headless=None):
        self.idx = idx
        self.path, self.kind = (path, kind) if path else job_binary()
        self.use_new_headless = (self.kind == "full") if use_new_headless is None else use_new_headless
        self.page = None
        self.jobs = 0
        self.launches = 0
        self._ctx = {}
        self._datadir = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------ proses
    def _launch(self):
        opts = ChromiumOptions()
        opts.set_browser_path(self.path)
        self._datadir = tempfile.mkdtemp(prefix="chromium-w%d-" % self.idx)
        opts.set_user_data_path(self._datadir)
        opts.auto_port()
        args = ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled",
                "--disable-infobars", f"--window-size={VIEW[0]},{VIEW[1]}", "--lang=en-US",
                "--disable-extensions", "--disable-background-networking", "--mute-audio", "--no-first-run"]
        if self.use_new_headless and config.HEADLESS:
            args.append("--headless=new")
        if self.kind == "shell":
            args.append("about:blank")  # chrome-headless-shell tidak membuka tab awal sendiri
        for a in args:
            opts.set_argument(a)
        opts.set_user_agent(browser.build_ua())
        self.page = ChromiumPage(opts)
        self.jobs = 0
        self.launches += 1

    def alive(self):
        try:
            return bool(self.page) and bool(self.page.browser.tab_ids is not None) and self.page.browser.states.is_alive
        except Exception:  # noqa: BLE001
            return False

    def mem(self):
        try:
            return tree_mem(self.page.browser.process_id) if self.page else {"rss": 0.0, "pss": 0.0}
        except Exception:  # noqa: BLE001
            return {"rss": 0.0, "pss": 0.0}

    def rss_mb(self):
        return self.mem()["pss"]  # PSS dipakai untuk batas BROWSER_MAX_MB

    def shutdown(self):
        with self._lock:
            self._shutdown()

    def _shutdown(self):
        if self.page:
            try:
                self.page.quit()
            except Exception:  # noqa: BLE001
                pass
        self.page = None
        self._ctx = {}
        if self._datadir:
            shutil.rmtree(self._datadir, ignore_errors=True)
            self._datadir = None

    def ensure(self):
        """Pastikan proses sehat; mulai ulang bila mati, sudah terlalu banyak job, atau terlalu boros memori."""
        with self._lock:
            why = None
            if not self.alive():
                why = "tidak aktif" if self.page else None
            elif self.jobs >= config.BROWSER_RECYCLE_JOBS:
                why = f"{self.jobs} job"
            elif self.jobs and self.rss_mb() > config.BROWSER_MAX_MB:
                why = "memori"
            if why:
                log.info("Browser worker %s dimulai ulang (%s)", self.idx, why)
                self._shutdown()
            if not self.page:
                try:
                    self._launch()
                except Exception:
                    if self.kind != "shell":
                        raise
                    log.warning("chrome-headless-shell gagal dijalankan; beralih ke Chromium penuh")
                    self._shutdown()
                    self.path, self.kind, self.use_new_headless = config.BROWSER_PATH, "full", True
                    self._launch()

    # --------------------------------------------------------------- job
    def acquire(self, block_media=True):
        self.ensure()
        try:
            tab = self._new_context_tab()
        except Exception:  # noqa: BLE001  (proses mungkin mati saat job sebelumnya)
            with self._lock:
                self._shutdown()
                self._launch()
            tab = self._new_context_tab()
        self.jobs += 1
        browser.apply_fingerprint(tab)
        try:
            tab.run_cdp("Emulation.setDeviceMetricsOverride", width=VIEW[0], height=VIEW[1], deviceScaleFactor=1, mobile=False)
            if block_media:
                tab.run_cdp("Network.enable")
                tab.run_cdp("Network.setBlockedURLs", urls=MEDIA_BLOCK)
        except Exception:  # noqa: BLE001
            pass
        return tab

    def _new_context_tab(self):
        tab = self.page.new_tab(new_context=True)  # konteks browser baru: cookie/storage terpisah dari job lain
        info = self.page.browser._run_cdp("Target.getTargetInfo", targetId=tab.tab_id)["targetInfo"]
        self._ctx[tab.tab_id] = info.get("browserContextId")
        return tab

    def release(self, tab):
        ctx = self._ctx.pop(getattr(tab, "tab_id", None), None)
        if ctx and self.page:
            try:
                self.page.browser._run_cdp("Target.disposeBrowserContext", browserContextId=ctx)
            except Exception:  # noqa: BLE001
                pass
