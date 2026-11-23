import os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os, sys, json
os.environ["DATA_DIR"]=os.path.join(os.environ["BARA_TMP"],"notif"); os.environ["API_KEY"]="k"
import shutil; shutil.rmtree(os.environ["DATA_DIR"],ignore_errors=True)
sys.path.insert(0,ROOT)
from app import notify as N, auth, store
from app.runner import Runner
sent=[]
def fake_dc(s,text,files=()): sent.append(("discord",s["discord_webhook"],text.split("\n")[0],len(files))); return True,None
def fake_tg(s,text): sent.append(("telegram",s["telegram_chat_id"],text.split("\n")[0],0)); return True,None
def fake_tgp(s,files): sent.append(("telegram-photos",s["telegram_chat_id"],"",len(files))); return True,None
N.send_discord=fake_dc; N.send_telegram=fake_tg; N.send_telegram_photos=fake_tgp
admin=auth.make_user("admin1","password1","admin"); a=auth.make_user("usera01","password1","user"); b=auth.make_user("userb01","password1","user")
def W():
    for u in (admin,a,b): store.user_save(u)
a["notify"]={"discord_enabled":True,"discord_webhook":"https://A","telegram_enabled":True,"telegram_token":"ta","telegram_chat_id":"chatA","notify_screenshot":True}
b["notify"]={"discord_enabled":True,"discord_webhook":"https://B","notify_screenshot":False}
W()
for _a in ({"id":"acA","name":"AccA","owner_id":a["id"],"schedules":[]},{"id":"acB","name":"AccB","owner_id":b["id"],"schedules":[]},{"id":"acAd","name":"AccAdmin","owner_id":admin["id"],"schedules":[]}): store.save_account(_a)
os.makedirs(os.environ["DATA_DIR"]+"/proofs/rr000001",exist_ok=True); open(os.environ["DATA_DIR"]+"/proofs/rr000001/1.jpg","wb").write(b"jpg")
G={"message":"hi","telegram_enabled":True,"telegram_token":"tg","telegram_chat_id":"chatG","discord_enabled":True,"discord_webhook":"https://G","notify_screenshot":False,"notify_all_accounts":True}
def run(acc,status="success",mode="send",**kw):
    return {"id":"rr000001","account":{"id":acc,"name":acc},"mode":mode,"trigger":"manual","label":None,"status":status,"started_at":"2026-11-16T07:00:00","finished_at":"2026-11-16T07:00:30","sent":1,"total":1,"message":None,"results":[{"contact":"X","ok":True,"proof":"1.jpg","sent_at":"07:00:10","evidence":{}}],"error":kw.get("error"),**kw}
r=Runner(); fails=[]
def ck(c,m): print(("ok   " if c else "FAIL ")+m); (not c) and fails.append(m)
def hosts(): return sorted({(k,t) for k,t,_,_ in sent})
def go(settings,run_): sent.clear(); r._notify(settings,run_); return list(sent)
# global channels only get admin-owned accounts; each user's runs only their own channels
s=go(G,run("acA")); ck(hosts()==sorted([("discord","https://A"),("telegram","chatA"),("telegram-photos","chatA")]),"A run -> only A personal: "+str(hosts()))
ck(not any(t in("https://G","chatG") for _,t,_,_ in s),"user run never reaches global channels")
ck(any(k=="discord" and t=="https://A" and n==1 for k,t,_,n in s),"A personal gets screenshot (personal flag true)")
s=go(G,run("acB")); ck(hosts()==[("discord","https://B")],"B run -> only B")
ck(not any(t=="https://B" for _,t,_,_ in go(G,run("acA"))),"B never receives A's notification")
s=go(G,run("acAd")); ck(sorted({t for _,t,_,_ in s})==["chatG","https://G"],"admin-owned run -> global channels")
ck(any(k=="discord" and t=="https://G" and n==0 for k,t,_,n in s),"global gets no screenshot (global flag false)")
# admin with personal channel + global: both, deduped when equal
admin["notify"]={"discord_enabled":True,"discord_webhook":"https://ADM","notify_screenshot":True}; W()
s=go(G,run("acAd")); ck(("discord","https://ADM") in hosts() and ("discord","https://G") in hosts(),"admin run -> personal + global")
admin["notify"]["discord_webhook"]="https://G"; W()
s=go(G,run("acAd")); ck(sum(1 for k,t,_,_ in s if k=="discord" and t=="https://G")==1,"duplicates suppressed")
admin["notify"]={}; W()
# cookie invalid routing
store.stores("acA").meta.write({})
s=go(G,run("acA",status="failed",mode="check",cookie_invalid=True,error="bad")); ck(hosts()==sorted([("discord","https://A"),("telegram","chatA")]) and "Cookie" in s[0][2],"cookie-invalid of A -> only A: "+str(hosts()))
store.stores("acAd").meta.write({})
s=go(G,run("acAd",status="failed",mode="check",cookie_invalid=True,error="bad")); ck(("discord","https://G") in hosts() and ("discord","https://A") not in hosts(),"cookie-invalid of admin -> global only")
s=go(G,run("acB",status="failed",mode="check",error="x")); ck(hosts()==[("discord","https://B")],"failed check of B -> only B")
a["disabled"]=True; W()
ck(go(G,run("acA"))==[],"disabled owner: nothing (global not used for user runs)")
a["disabled"]=False; W()
ck(go(G,run("acA",mode="test"))==[] and go(G,run("acA",status="cancelled"))==[],"test/cancelled silent")
print("FAILS",fails)
import sys as _sys
_sys.exit(1 if fails else 0)
