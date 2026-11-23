import os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys, threading, threading as T, time, http.server, socketserver
FX=os.path.join(ROOT,"tests","fixtures","login")
os.environ.update(DATA_DIR=os.path.join(os.environ["BARA_TMP"],"scan"), API_KEY="k", BROWSER_PATH=os.environ["BROWSER_PATH"])
sys.path.insert(0,ROOT)
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s,*a,**k): super().__init__(*a,directory=FX,**k)
    def log_message(s,*a): pass
socketserver.TCPServer.allow_reuse_address=True
srv=socketserver.ThreadingTCPServer(("127.0.0.1",0),H); threading.Thread(target=srv.serve_forever,daemon=True).start()
BASE=f"http://127.0.0.1:{srv.server_address[1]}"
from app import config, store
from app.bot import StreakBot
config.TIKTOK_URL=BASE+"/home.html"; config.TIKTOK_MESSAGES_URL=BASE+"/messages.html"
fails=[]
def ck(c,m):
    print(("ok   " if c else "FAIL ")+m); (not c) and fails.append(m)
class Store:
    def __init__(s): s.d=[{"name":"sessionid","value":"x","domain":"127.0.0.1","path":"/"}]
    def read(s): return s.d
    def write(s,d): s.d=d
st=dict(store.get_settings(),page_load_wait=1,element_wait=1)
def scan(limit):
    bot=StreakBot(st,lambda *a,**k:None,T.Event(),Store(),check_only=True,account_id="scantest")
    return bot.scan_contacts(limit)
items=scan(500)
ids=[i["id"] for i in items]
ck(len(items)==120 and len(set(ids))==120,f"scrolls the virtual list and collects every conversation once ({len(items)})")
ck(items[0]["nick"]=="Teman 0" and items[-1]["nick"]=="Teman 119","nickname and order preserved: "+items[0]["nick"]+" .. "+items[-1]["nick"])
ck(all(i["time"] and ":" in i["time"] for i in items),"last-message time collected")
ck(ids==[f"conv{i}" for i in range(120)],"conv-ids collected")
small=scan(40)
ck(len(small)==40,f"limit respected ({len(small)})")
print("FAILS",fails)
sys.exit(1 if fails else 0)
