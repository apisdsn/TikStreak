import os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json, os, shutil, subprocess, sys, sqlite3, time
R=os.path.join(os.environ["BARA_TMP"],"mig"); shutil.rmtree(R,ignore_errors=True); os.makedirs(R)
sys.path.insert(0,ROOT)
os.environ.update(DATA_DIR=os.path.join(os.environ["BARA_TMP"],"mig-hash"),API_KEY="k")
from app import auth
fails=[]
def ck(c,m):
    print(("ok   " if c else "FAIL ")+m); (not c) and fails.append(m)
def wj(p,d):
    os.makedirs(os.path.dirname(p),exist_ok=True); json.dump(d,open(p,"w"))
# --- A: pre-auth multi-account (copy of data-ios)
A=R+"/A"; shutil.copytree(os.path.join(ROOT,"tests","fixtures","preauth"),A)
# --- B: auth-era with users, sessions, owners, notify, history, fired keys, s1 legacy id
B=R+"/B"; os.makedirs(B)
u1=auth.make_user("admin","password1","admin"); u2=auth.make_user("budi","budipass1","user")
u1["notify"]={"discord_enabled":True,"discord_webhook":"https://discord.com/api/webhooks/1/SECRETHOOK","telegram_token":"TGSECRET123456"}
wj(B+"/users.json",[u1,u2])
wj(B+"/sessions.json",{"h1":{"user_id":u1["id"],"created":time.time(),"expires":time.time()+3600},"old":{"user_id":u2["id"],"created":1,"expires":2}})
wj(B+"/settings.json",{"message":"Halo","timezone":"Asia/Jakarta","discord_webhook":"https://discord.com/api/webhooks/9/GLOBALHOOK","telegram_token":"GLOBALTG98765","keepalive_enabled":False,"notify_all_accounts":True})
wj(B+"/accounts.json",[{"id":"a1","name":"Utama","owner_id":u1["id"],"schedules":[{"id":"s1","enabled":True,"time":"07:00","message":"","contacts":None},{"id":"x2","enabled":False,"time":"19:30","message":"M","contacts":["Rina"]}]},
 {"id":"a2","name":"Utama","owner_id":u2["id"],"schedules":[]},{"id":"a3","name":"Orphan","owner_id":"missing","schedules":[]}])
wj(B+"/accounts/a1/cookies.json",[{"name":"sessionid","value":"COOKIESECRETVALUE","domain":".tiktok.com"}])
wj(B+"/accounts/a1/contacts.json",["Rina","Dimas","rina"])
wj(B+"/accounts/a1/meta.json",{"last_ok":"2026-11-01T10:00:00","fired":{"s1":"2026-11-01 07:00"},"last_schedule":"2026-10-01 07:00","last_check":123.0})
wj(B+"/accounts/a1/convs.json",{"rina":"conv1"})
wj(B+"/history.json",[{"id":"%08x"%i,"account":{"id":"a1" if i%2 else "a2","name":"Utama"},"mode":"send","trigger":"manual","by":"admin","label":None,"status":"success","started_at":"2026-11-%02dT07:00:00"%(1+i%20),"finished_at":"2026-11-%02dT07:01:00"%(1+i%20),"sent":2,"total":2,"error":None,"results":[{"contact":"Rina","ok":True}],"logs":[{"t":"07:00:01","level":"info","msg":"x"}]} for i in range(30)])
os.makedirs(B+"/proofs/00000001",exist_ok=True); open(B+"/proofs/00000001/1.jpg","wb").write(b"jpg")
# --- C: legacy single account (settings schedule_time, root files)
C=R+"/C"; os.makedirs(C)
wj(C+"/settings.json",{"message":"Legacy","schedule_enabled":True,"schedule_time":"06:30","telegram_token":"LEGACYTG55555"})
wj(C+"/cookies.json",[{"name":"sessionid","value":"LEGACYCOOKIE","domain":".tiktok.com"}])
wj(C+"/contacts.json",["Ayu","Budi"]); wj(C+"/meta.json",{"last_schedule":"2026-10-30 06:30","last_ok":"2026-10-30T06:31:00"})
wj(C+"/history.json",[{"id":"deadbeef","account":{"id":"main","name":"Utama"},"mode":"send","trigger":"schedule","label":"06:30","status":"partial","started_at":"2026-10-30T06:30:00","finished_at":"2026-10-30T06:32:00","sent":1,"total":2,"error":None,"results":[],"logs":[]}])
CODE='''
import json,os,sys
sys.path.insert(0,os.getcwd())
from app import store, db
out={"accounts":len(store.list_accounts()),"users":store.users_count(),"runs":db.q1("select count(*) c from runs")["c"],
"contacts":{a["id"]:store.stores(a["id"]).contacts.read() for a in store.list_accounts()},
"cookies":{a["id"]:len(store.stores(a["id"]).cookies.read()) for a in store.list_accounts()},
"meta":{a["id"]:store.stores(a["id"]).meta.read() for a in store.list_accounts()},
"scheds":{a["id"]:[(s["id"],s["time"],s["enabled"],s["contacts"]) for a in [a] for s in a["schedules"]] for a in store.list_accounts()},
"settings":store.get_settings(),"owners":{a["id"]:a["owner_id"] for a in store.list_accounts()},"names":{a["id"]:a["name"] for a in store.list_accounts()},
"sessions":db.q1("select count(*) c from sessions")["c"],"notify":[u["notify"] for u in store.users_all()],"ver":db.q1("pragma user_version")[0]}
print(json.dumps(out))
'''
def run(d):
    e=dict(os.environ,DATA_DIR=d,API_KEY="k"); 
    p=subprocess.run([sys.executable,"-c",CODE],env=e,capture_output=True,text=True,cwd=ROOT); 
    if p.returncode: print(p.stderr[-800:]); 
    return json.loads(p.stdout.strip().splitlines()[-1])
# A
NA=len(json.load(open(A+"/history.json")))
a=run(A); ck(a["accounts"]==2 and a["runs"]==NA and a["ver"]==len(__import__("app.db",fromlist=["MIGRATIONS"]).MIGRATIONS),"A: pre-auth dir migrated "+str({k:a[k] for k in('accounts','runs')}))
ck(a["contacts"]["main"]==json.load(open(A+"/backup-json-"+[f for f in os.listdir(A) if f.startswith("backup-json")][0].split("backup-json-")[1]+"/accounts/main/contacts.json")),"A: contacts preserved")
ck(not os.path.exists(A+"/accounts.json") and not os.path.exists(A+"/history.json") and any(f.startswith("backup-json-") for f in os.listdir(A)),"A: json moved to backup folder")
ck(os.path.isdir(A+"/proofs") and os.path.exists(A+"/last_run.jpg"),"A: proofs/screenshot stay in place")
a2=run(A); ck(a2["accounts"]==2 and a2["runs"]==NA and len([f for f in os.listdir(A) if f.startswith("backup-json")])==1,"A: idempotent second start")
# B
b=run(B); ck(b["users"]==2 and b["accounts"]==3 and b["runs"]==30 and b["sessions"]==1,"B: counts users/accounts/runs/sessions(expired dropped)")
ck(b["contacts"]["a1"]==["Rina","Dimas"],"B: contacts deduped case-insensitively")
ck(b["meta"]["a1"]["fired"]=={"s1":"2026-11-01 07:00"} and b["meta"]["a1"]["last_schedule"]=="2026-10-01 07:00","B: fired + last_schedule meta kept")
ck(b["scheds"]["a1"][0][0]=="s1" and b["scheds"]["a1"][1][3]==["Rina"],"B: legacy s1 schedule id + per-contact schedule kept")
ck(b["owners"]["a3"] is None and b["names"]["a2"]=="Utama","B: orphan owner nulled; same name allowed across owners")
ck("legacy" not in json.dumps(b["settings"]).lower() and "notify_all_accounts" not in b["settings"] and b["settings"]["discord_webhook"].endswith("GLOBALHOOK"),"B: settings migrated, legacy key dropped, secret decrypts")
ck(b["notify"][0]["discord_webhook"].endswith("SECRETHOOK"),"B: user notify secrets round-trip")
raw=open(B+"/streak.db","rb").read()+(open(B+"/streak.db-wal","rb").read() if os.path.exists(B+"/streak.db-wal") else b"")
for needle in (b"COOKIESECRETVALUE",b"SECRETHOOK",b"GLOBALHOOK",b"TGSECRET123456",b"GLOBALTG98765"):
    ck(needle not in raw,f"B: raw db has no plaintext {needle.decode()}")
ck(os.path.exists(B+"/secret.key") and oct(os.stat(B+"/secret.key").st_mode)[-3:]=="600","B: secret.key created chmod 600")
# C
c=run(C); ck(c["accounts"]==1 and c["names"]["main"]=="Utama" and c["scheds"]["main"][0][:3]==("s1","06:30",True) or c["scheds"]["main"][0][:3]==["s1","06:30",True],"C: legacy single account -> main with s1 schedule: "+str(c["scheds"]))
ck(c["contacts"]["main"]==["Ayu","Budi"] and c["cookies"]["main"]==1 and c["runs"]==1,"C: root contacts/cookies/history imported")
raw=open(C+"/streak.db","rb").read()
ck(b"LEGACYCOOKIE" not in raw and b"LEGACYTG55555" not in raw,"C: encrypted at rest")
# fresh empty dir
E=R+"/E"; os.makedirs(E); e=run(E); ck(e["accounts"]==0 and e["users"]==0,"E: empty dir starts clean")
print("FAILS",fails)
import sys as _sys
_sys.exit(1 if fails else 0)
