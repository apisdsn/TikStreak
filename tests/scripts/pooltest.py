import os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json, os, sys, threading, time, http.server, socketserver
FX=os.path.join(ROOT,"tests","fixtures","login")
os.environ.update(DATA_DIR=os.path.join(os.environ["BARA_TMP"],"pool"), API_KEY="k", BROWSER_PATH=os.environ["BROWSER_PATH"])
sys.path.insert(0,ROOT)
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s,*a,**k): super().__init__(*a,directory=FX,**k)
    def log_message(s,*a): pass
socketserver.TCPServer.allow_reuse_address=True
srv=socketserver.ThreadingTCPServer(("127.0.0.1",8898),H); threading.Thread(target=srv.serve_forever,daemon=True).start()
from app import pool, config
fails=[]
def ck(c,m):
    print(("ok   " if c else "FAIL ")+m); (not c) and fails.append(m)
URL="http://127.0.0.1:8898/cookie.html"
def cookie_of(tab):
    tab.get(URL); time.sleep(0.2); return tab.run_js("return document.getElementById('c').textContent")
chrome=pool.BrowserHolder(0,os.environ["BROWSER_PATH"],"full",True)
# --- isolation
a=chrome.acquire(); b=chrome.acquire()   # dua konteks bersamaan
a.get(URL); a.set.cookies({"name":"acct","value":"AAA","domain":"127.0.0.1","path":"/"})
ck("acct=AAA"==cookie_of(a),"context A sees its own cookie")
ck(cookie_of(b)=="","context B (open at the same time) sees nothing")
b.get(URL); b.set.cookies({"name":"acct","value":"BBB","domain":"127.0.0.1","path":"/"}); ck(cookie_of(b)=="acct=BBB","B sets its own")
ck(cookie_of(a)=="acct=AAA","A unchanged")
ca=[c["value"] for c in a.run_cdp("Network.getAllCookies")["cookies"]]; cb=[c["value"] for c in b.run_cdp("Network.getAllCookies")["cookies"]]
ck(ca==["AAA"] and cb==["BBB"],f"Network.getAllCookies scoped per context: {ca} {cb}")
chrome.release(a); chrome.release(b)
c=chrome.acquire(); ck(cookie_of(c)=="","new context after dispose has no leftover cookies")
chrome.release(c)
# media blocking active
t=chrome.acquire(block_media=True); ck(True,"acquire with media block ok"); chrome.release(t)
chrome.shutdown()
# --- timing / memory: process per job vs context reuse, full vs shell
def job(holder_factory, reuse, n=3):
    t0=time.time(); starts=[]; peak=0; peak2=0; per=[]
    h=holder_factory() if reuse else None
    for i in range(n):
        s=time.time()
        hh=h or holder_factory()
        tab=hh.acquire(); startup=time.time()-s
        tab.get(URL); time.sleep(1.0)   # "job" ringan: muat halaman
        m=hh.mem(); peak=max(peak,m['rss']); peak2=max(peak2,m['pss'])
        hh.release(tab)
        if not reuse: hh.shutdown()
        per.append(time.time()-s); starts.append(startup)
    if h: h.shutdown()
    return {"first_startup":round(starts[0],2),"avg_startup":round(sum(starts)/len(starts),2),"avg_job":round(sum(per)/len(per),2),"peak_rss_sum_mb":round(peak),"peak_pss_mb":round(peak2)}
res={}
full=lambda: pool.BrowserHolder(0,os.environ["BROWSER_PATH"],"full",True)
sp=pool.shell_path(); print("shell:",sp)
res["full/process-per-job"]=job(full,False)
res["full/context-reuse"]=job(full,True)
if sp:
    shell=lambda: pool.BrowserHolder(0,sp,"shell",False)
    res["shell/process-per-job"]=job(shell,False)
    res["shell/context-reuse"]=job(shell,True)
for k,v in res.items(): print(k,json.dumps(v))
json.dump(res,open(os.path.join(os.environ["BARA_TMP"],"pool-timing.json"),"w"))
print("FAILS",fails)
# --- bot-like fixture flow on both binaries (cookies, type text, click via JS, screenshot, media blocking)
def flow(h):
    t=h.acquire(block_media=True); t.get("http://127.0.0.1:8898/flow.html"); time.sleep(1.0)
    r={}
    el=t.ele("#msg"); el.click(); t.run_cdp("Input.insertText",text="Halo Bara"); t.run_js("arguments[0].click();",t.ele("#send"))
    time.sleep(0.2); r["typed"]=t.ele("#log").text
    r["shot"]=len(t.run_cdp("Page.captureScreenshot",format="jpeg",quality=60)["data"])>500
    r["img"]=t.run_js("return document.getElementById('img').naturalWidth")>0
    r["media"]=t.run_js("return document.getElementById('media').textContent")
    t.set.cookies({"name":"s","value":"1","domain":"127.0.0.1","path":"/"}); r["cookies"]=[c["name"] for c in t.run_cdp("Network.getAllCookies")["cookies"]]
    r["ua"]=t.run_js("return navigator.userAgent"); r["wd"]=t.run_js("return navigator.webdriver")
    h.release(t); return r
rs={}
for name,mk in (("full",full),):
    h=mk(); rs[name]=flow(h); h.shutdown()
if sp:
    h=pool.BrowserHolder(0,sp,"shell",False); rs["shell"]=flow(h); h.shutdown()
for k,v in rs.items(): print("flow",k,json.dumps(v))
for k,v in rs.items():
    ck(v["typed"]=="Halo Bara;" and v["shot"] and v["img"] and v["media"]=="blocked" and v["cookies"]==["s"] and v["wd"] is False,f"{k}: type/click/screenshot/images ok, media blocked, cookies scoped, webdriver false")
if len(rs)==2: ck(rs["full"]["ua"]==rs["shell"]["ua"] and "Headless" not in rs["shell"]["ua"],"UA identical across binaries, no 'Headless'")
print("FAILS2",fails)
import sys as _sys
_sys.exit(1 if fails else 0)
