import os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json, os, sys, threading, time, http.server, socketserver
FX=os.path.join(ROOT,"tests","fixtures","login")
os.environ.update(DATA_DIR=os.path.join(os.environ["BARA_TMP"],"lt"), API_KEY="k", BROWSER_PATH=os.environ["BROWSER_PATH"], LOGIN_START_URL="http://127.0.0.1:8899/index.html")
sys.path.insert(0,ROOT)
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s,*a,**k): super().__init__(*a,directory=FX,**k)
    def log_message(s,*a): pass
    def do_GET(s):
        if s.path.startswith("/echo"):
            b=json.dumps({k.lower():v for k,v in s.headers.items()}).encode(); s.send_response(200); s.send_header("Content-Type","application/json"); s.send_header("Content-Length",str(len(b))); s.end_headers(); s.wfile.write(b); return
        if s.path.startswith("/missing"): s.send_response(404); s.end_headers(); return
        return super().do_GET()
socketserver.TCPServer.allow_reuse_address=True
srv=socketserver.ThreadingTCPServer(("127.0.0.1",8899),H); threading.Thread(target=srv.serve_forever,daemon=True).start()
from app.login import LoginSession
fails=[]
def ck(c,m):
    print(("ok   " if c else "FAIL ")+m); (not c) and fails.append(m)
s=LoginSession(); s.start("t"); time.sleep(2.5)
import sys as _s
if len(_s.argv)>1:
    t0=s._tab()
    for sel in ("#openbtn","#alertbtn","#pwd","#errbtn"): print(sel,t0.run_js(f"const r=document.querySelector('{sel}').getBoundingClientRect();return [r.x,r.y,r.width,r.height]"))
    s.stop(); _s.exit()
def pos(tab,sel): return tab.run_js(f"const r=document.querySelector('{sel}').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]")
def click(sel):
    x,y=pos(s._tab(),sel); s.input({"type":"click","x":x,"y":y})
def text(tab,sel="#out"): return tab.run_js(f"return document.querySelector('{sel}').textContent")
def waitfor(fn,t=4):
    end=time.time()+t
    while time.time()<end:
        try:
            if fn(): return True
        except Exception: pass
        time.sleep(0.2)
    return False
st=s.status(); ck(st["active"] and st["tabs"]==1 and "127.0.0.1" in st["url"] and "?" not in st["url"],"status url/tabs: "+json.dumps({k:st[k] for k in("url","tabs","tab")}))
# 1. popup
click("#openbtn"); ok=waitfor(lambda:(s.frame(),s.status()["tabs"]==2)[1]); st=s.status()
ck(ok and st["tab"]==2 and "second.html" in st["url"],"follows new tab: "+json.dumps({k:st[k] for k in("url","tabs","tab")}))
click("#second"); ck(waitfor(lambda:text(s._tab())=="second-clicked"),"click registers in new tab")
ck(len(s.frame())>1000,"frame from new tab")
# viewport override applied to new tab
ck(s._tab().run_js("return [innerWidth,innerHeight]")==[1000,700],"new tab viewport 1000x700 "+str(s._tab().run_js("return [innerWidth,innerHeight]")))
# 2. switch back + alert
s.input({"type":"nav","action":"tab","index":1}); ck(s.status()["tab"]==1,"switch back to tab 1")
click("#alertbtn"); ck(waitfor(lambda:text(s._tab())=="after-alert"),"alert auto-handled, page continues")
ck(any(d["kind"]=="dialog" and "halo dari fixture" in d["msg"] for d in s.status()["diag"]),"dialog recorded in diag")
# 3. pointer sequence/hover modal
click("#pwd"); ck(waitfor(lambda:text(s._tab(),"#mout")=="row-ok"),"hover+pointerdown/up modal registers")
# 4. diagnostics
click("#errbtn"); time.sleep(1); d=s.status()["diag"]
ck(any(x["kind"]=="console" and "boom-test" in x["msg"] for x in d),"console error recorded")
ck(any(x["kind"]=="network" and "404" in x["msg"] and "/missing" in x["msg"] and "secret" not in x["msg"] and "abc123" not in x["msg"] for x in d),"HTTP 404 path recorded without query: "+json.dumps([x["msg"] for x in d if x["kind"]=="network"]))
ck(not any("secret" in json.dumps(x) for x in d),"no query strings anywhere in diag")
ck(len(d)<=20,"diag capped")
# 5. tab close fallback
s.input({"type":"nav","action":"tab","index":2}); time.sleep(0.5)
s._tab().run_js("window.close()"); waitfor(lambda:(s.frame(),s.status()["tabs"]==1)[1]); st=s.status()
ck(st["tabs"]==1 and st["tab"]==1,"active tab closed -> falls back: "+json.dumps({k:st[k] for k in("tabs","tab")}))
# 6. nav buttons
s._tab().get("http://127.0.0.1:8899/ua.html"); time.sleep(1.5)
s.input({"type":"nav","action":"back"}); time.sleep(1.2); ck("index.html" in s.status()["url"],"back works: "+s.status()["url"])
s.input({"type":"nav","action":"login"}); time.sleep(1); ck("index.html" in s.status()["url"],"login nav")
# 7. fingerprint
s._tab().get("http://127.0.0.1:8899/ua.html"); waitfor(lambda:s._tab().title=="ready",8)
lines=text(s._tab(),"#ua").split("\n"); info=json.loads(lines[0]); echo=json.loads(lines[1])
print(json.dumps(info)[:400]); print(json.dumps({k:echo.get(k) for k in('user-agent','sec-ch-ua','sec-ch-ua-platform','sec-ch-ua-mobile')}))
ck("Headless" not in info["ua"] and "X11; Linux" in info["ua"] and "Windows" not in info["ua"],"UA is Linux Chrome without Headless")
ck(info["platform"]=="Linux x86_64","navigator.platform Linux")
ck(info["webdriver"] is False,"navigator.webdriver false")
ck(info["uadPlatform"]=="Linux" and info["hi"].get("platform")=="Linux" and not info["mobile"],"userAgentData platform Linux")
ck(all("Headless" not in b["brand"] for b in info["brands"]) and any(b["brand"]=="Google Chrome" for b in info["brands"]),"brands no Headless")
ck(echo["user-agent"]==info["ua"],"request UA header == navigator.userAgent")
ck(echo.get("sec-ch-ua-platform")=='"Linux"' and "Headless" not in echo.get("sec-ch-ua",""),"Sec-CH-UA headers consistent")
major=info["ua"].split("Chrome/")[1].split(".")[0]
ck(all(b["version"]==major for b in info["brands"] if b["brand"] in("Chromium","Google Chrome")),"brand versions match UA major "+major)
s.stop(); ck(not s.active,"stopped")
# 8. send-browser (bot) fingerprint
import threading as T
from app.bot import StreakBot
b=StreakBot({"message":"x","page_load_wait":1,"element_wait":1,"send_delay":0,"notify_screenshot":False},print,T.Event(),None)
b._create_browser(); b.page.get("http://127.0.0.1:8899/ua.html"); waitfor(lambda:b.page.title=="ready",8)
lines=b.page.run_js("return document.getElementById('ua').textContent").split("\n"); info2=json.loads(lines[0])
ck(info2["ua"]==info["ua"] and info2["platform"]=="Linux x86_64" and info2["webdriver"] is False,"send browser same UA/platform as login browser")
try: b.page.quit()
except Exception: pass
print("FAILS",fails)
import sys as _sys
_sys.exit(1 if fails else 0)
