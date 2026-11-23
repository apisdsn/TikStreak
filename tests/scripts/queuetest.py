import os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os, sys, time, shutil, threading, json
D=os.path.join(os.environ["BARA_TMP"],"queue"); shutil.rmtree(D,ignore_errors=True)
os.environ.update(DATA_DIR=D, API_KEY="k", QUEUE_JITTER_MIN="0", QUEUE_JITTER_MAX="0")
sys.path.insert(0,ROOT)
from app import auth, store, jobs, runner as R, db, config
from app.runner import runner
fails=[]
def ck(c,m):
    print(("ok   " if c else "FAIL ")+m); (not c) and fails.append(m)
admin=auth.make_user("admin1","password1","admin"); ua=auth.make_user("usera01","password1","user"); ub=auth.make_user("userb01","password1","user")
for u in (admin,ua,ub): store.user_save(u)
_n=[0]
def acct(owner,name=None):
    _n[0]+=1; a=store.create_account(name or f"acc{_n[0]}",owner["id"]); store.stores(a["id"]).contacts.write(["Rina","Dimas"]); return a
log=[]; lock=threading.Lock(); conc={"now":0,"max":0}
def fake(dur=0.2):
    def ex(run,job,cancel,gp):
        with lock:
            conc["now"]+=1; conc["max"]=max(conc["max"],conc["now"]); log.append(("start",job["account_id"],job["kind"],job["trigger"],time.time()))
        end=time.time()+dur
        while time.time()<end:
            if cancel.is_set(): run["status"]="cancelled"; break
            time.sleep(0.02)
        else: run["status"]="success"; run["sent"]=run["total"]=2
        with lock:
            conc["now"]-=1; log.append(("end",job["account_id"],job["kind"],job["trigger"],time.time()))
        return None
    return ex
sent=[]
R.notify=lambda t,title,lines=(),files=(): sent.append((t.get("discord_webhook") or t.get("telegram_chat_id"),title))
def start(workers,jitter=(0,0),dur=0.2):
    log.clear(); conc.update(now=0,max=0); runner.executor=fake(dur); runner.jitter=jitter; runner.start_workers(workers=workers,scheduler=False)
def stop(): runner.shutdown()
def wait_idle(t=20):
    end=time.time()+t
    while time.time()<end:
        c=jobs.counts()
        if c["queued"]+c["running"]==0 and runner._runs=={}: return True
        time.sleep(0.05)
    return False
now=time.time()
# 1. ordering and priority (enqueue before workers start)
k=acct(admin); s1=acct(admin); s2=acct(ua); m=acct(ub)
jobs.enqueue(k["id"],admin["id"],"check","keepalive")
jobs.enqueue(s2["id"],ua["id"],"send","schedule",label="08:00",due_at=now-100)
jobs.enqueue(s1["id"],admin["id"],"send","schedule",label="07:00",due_at=now-500)
jobs.enqueue(m["id"],ub["id"],"send","manual",by="userb01")
store.save_settings({**store.get_settings(),"keepalive_enabled":False})
start(1); ck(wait_idle(),"queue drains")
order=[(e[1],e[3]) for e in log if e[0]=="start"]; stop()
ck(order==[(m["id"],"manual"),(s1["id"],"schedule"),(s2["id"],"schedule"),(k["id"],"keepalive")],"priority: manual > scheduled (by due_at) > keepalive: "+str([o[1] for o in order]))
# 2. one job per account
a=acct(ua)
jobs.enqueue(a["id"],ua["id"],"send","manual")
try: jobs.enqueue(a["id"],ua["id"],"send","manual"); dup=False
except jobs.Duplicate: dup=True
ck(dup,"second active job for same (account, kind) rejected")
jobs.enqueue(a["id"],ua["id"],"check","manual")   # beda kind boleh antre, tetapi tidak boleh jalan bersamaan
b=acct(ub); jobs.enqueue(b["id"],ub["id"],"send","manual")
start(2,dur=0.4); ck(wait_idle(),"2 workers drain")
iv={}
for e in log: iv.setdefault((e[1],e[2]),{})[e[0]]=e[4]
x,y=iv[(a["id"],"send")],iv[(a["id"],"check")]
ck(x["end"]<=y["start"]+0.05 or y["end"]<=x["start"]+0.05,"same account never runs two jobs at once")
stop()
# 3. concurrency bound / speed at workers=1 vs 2
def burst(workers):
    accs=[acct(ua) for _ in range(4)]
    for ac in accs: jobs.enqueue(ac["id"],ua["id"],"send","manual")
    t0=time.time(); start(workers,dur=0.5); wait_idle(); dt=time.time()-t0; mx=conc["max"]; stop(); return dt,mx
t1,m1=burst(1); t2,m2=burst(2)
ck(m1==1 and m2==2,f"max concurrency equals workers ({m1},{m2})")
ck(t2<t1*0.75,f"2 workers faster than 1 ({t1:.2f}s vs {t2:.2f}s)")
# 4. restart recovery
r1=acct(ua); r2=acct(ub)
j1=jobs.enqueue(r1["id"],ua["id"],"send","manual"); j2=jobs.enqueue(r2["id"],ub["id"],"send","schedule",label="06:00",due_at=time.time()-5*3600)
db.x("UPDATE jobs SET status='running', started_at=? WHERE id IN (?,?)",(time.time(),j1["id"],j2["id"]))
nruns=db.q1("select count(*) c from runs where account_id=?",(r2["id"],))["c"]
start(1); wait_idle(); stop()
ck(jobs.get(j1["id"])["status"]=="done","running job within window goes back to queue and completes")
ck(jobs.get(j2["id"])["status"]=="expired","old scheduled running job expires after restart")
missed=[r for r in store.query_runs(ub["id"],r2["id"])[0] if r["status"]=="expired"]; ck(len(missed)==1,"expired job recorded as 'Terlewat' run")
# 5. expiry of queued overdue + notification to owner
sent.clear(); ub["notify"]={"discord_enabled":True,"discord_webhook":"https://B","notify_screenshot":False}; store.user_save(ub)
e1=acct(ub); je=jobs.enqueue(e1["id"],ub["id"],"send","schedule",label="05:00",due_at=time.time()-4*3600)
start(1); wait_idle(); stop()
ck(jobs.get(je["id"])["status"]=="expired","overdue queued scheduled job expired")
ck(any(t=="https://B" and "Terlewat" in title for t,title in sent),"owner notified of missed schedule: "+str(sent))
run=[r for r in store.query_runs(ub["id"],e1["id"])[0]][0]; ck(run["status"]=="expired" and "Antrean" in (run["error"] or ""),"missed run has reason: "+str(run["error"]))
# 6. midnight warning once per day
from datetime import datetime
sent.clear(); ua["notify"]={"discord_enabled":True,"discord_webhook":"https://A","notify_screenshot":False}; store.user_save(ua)
orig=runner.avg_duration; runner.avg_duration=lambda *a,**k: 3600.0
tzname=config.DEFAULT_TZ
due=datetime.now(R._tz({})).replace(hour=23,minute=50,second=0,microsecond=0).timestamp()
for _ in range(2):
    ac=acct(ua); jobs.enqueue(ac["id"],ua["id"],"send","schedule",label="23:50",due_at=due)
runner.workers=1
runner.check_midnight(); n1=len([1 for t,ti in sent if "Tengah Malam" in ti and t=="https://A"])
runner.check_midnight(); n2=len([1 for t,ti in sent if "Tengah Malam" in ti and t=="https://A"])
ck(n1==1 and n2==1,f"midnight warning sent once per day ({n1},{n2})")
from app.store import kv_set
kv_set("qwarn:"+ua["id"],"1999-01-01"); runner.check_midnight(); n3=len([1 for t,ti in sent if "Tengah Malam" in ti and t=="https://A"])
ck(n3==2,"warns again on a new day")
runner.avg_duration=orig
db.x("DELETE FROM jobs WHERE status='queued'")
# 7. jitter bounds
accs=[acct(ua) for _ in range(4)]
for ac in accs: jobs.enqueue(ac["id"],ua["id"],"send","manual")
start(1,jitter=(1,2),dur=0.3); wait_idle(30)
starts=[e[4] for e in log if e[0]=="start"]; ends=[e[4] for e in log if e[0]=="end"]; stop()
gaps=[starts[i+1]-ends[i] for i in range(len(starts)-1)]
ck(len(gaps)==3 and all(0.95<=g<=2.7 for g in gaps),f"jitter pause between jobs within [1,2]s: {[round(g,2) for g in gaps]}")
# 8. keepalive guard near due schedule
g=acct(admin); store.save_account({**store.get_account(g["id"]),"schedules":[{"id":"s9","enabled":True,"time":datetime.now(R._tz({})).strftime("%H:%M"),"message":"","contacts":None}]})
kj=jobs.enqueue(g["id"],admin["id"],"check","keepalive")
runner.executor=fake(0.1); got=runner.next_job()
ck(got is None,"keepalive does not start while a scheduled send is due within 10 minutes")
store.save_account({**store.get_account(g["id"]),"schedules":[]})
got=runner.next_job(); ck(got is not None and got["id"]==kj["id"],"keepalive starts when no send is near")
jobs.finish(kj["id"],"done")
# 9. cancel queued and running
c1=acct(ua); jc=jobs.enqueue(c1["id"],ua["id"],"send","manual")
ck(runner.cancel_job(jc["id"],ub["id"]) is False and runner.cancel_job(jc["id"],ua["id"]) is True and jobs.get(jc["id"])["status"]=="cancelled","cancel queued job (owner only)")
c2=acct(ua); jobs.enqueue(c2["id"],ua["id"],"send","manual"); start(1,dur=5)
for _ in range(100):
    if runner.running_runs(): break
    time.sleep(0.05)
ck(runner.stop(ub["id"])==0 and runner.stop(ua["id"],c2["id"])==1,"stop running job affects only the owner's")
wait_idle(); r=store.query_runs(ua["id"],c2["id"])[0][0]; ck(r["status"]=="cancelled","running job cancelled"); stop()
# 10. isolation of queue info
x1=acct(ua); x2=acct(ub); jobs.enqueue(x1["id"],ua["id"],"send","manual"); jobs.enqueue(x2["id"],ub["id"],"send","manual")
va=runner.view_for(ua["id"]); vb=runner.view_for(ub["id"])
ck(all(j["account_id"]==x1["id"] for j in va["mine"]) and all(j["account_id"]==x2["id"] for j in vb["mine"]),"each user only sees own jobs")
ck(set(va)=={"mine","queued","running","workers"} and va["queued"]>=2,"others appear only as aggregate counts")
ck(va["mine"][0]["position"]>=1 and va["mine"][0]["eta"] and ":" in va["mine"][0]["eta"],"position and ETA present: "+json.dumps(va["mine"][0]))
db.x("DELETE FROM jobs WHERE status='queued'")
# 11. login session blocks account
l=acct(ua); jl=jobs.enqueue(l["id"],ua["id"],"send","manual")
runner._login_accounts=lambda: {l["id"]}
ck(runner.next_job() is None,"account with active remote login is skipped")
runner._login_accounts=lambda: set(); got=runner.next_job(); ck(got and got["id"]==jl["id"],"claimed once login ends")
jobs.finish(jl["id"],"done")
# 12. ETA fallback and history average
ck(abs(runner.avg_duration("nope","send",4)-140)<0.1 and runner.avg_duration("nope","check")==30,"ETA fallback: 30s/contact + 20s, check 30s")
print("FAILS",fails)
import sys as _sys
_sys.exit(1 if fails else 0)
