import os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
import requests, json, sys, time, os
import os
B=os.environ.get("BARA_BASE","http://127.0.0.1:8791"); H={"X-Requested-With":"streak-panel"}; KEY={"X-API-Key":"testkey123"}
D=os.environ.get("BARA_DATA","")
fails=[]
def ck(c,m):
    print(("ok   " if c else "FAIL ")+m)
    if not c: fails.append(m)
def S(): return requests.Session()
def req(s,m,p,j=None,h=H,**k): return s.request(m,B+p,json=j,headers=h,**k)
def login(u,p):
    s=S(); r=req(s,"POST","/api/auth/login",{"username":u,"password":p}); assert r.status_code==200,(u,r.text); return s
def idle(s):
    time.sleep(0.5)
    for _ in range(90):
        st=s.get(B+"/api/status").json()
        if not st["running"] and not st["queue"]["mine"]: return
        time.sleep(1)

# ---- setup / migration / csrf
ck(requests.get(B+"/api/status").status_code==401,"401 without auth")
ck(requests.get(B+"/api/status",headers=KEY).status_code==200,"api key works before setup")
adm=S()
ck(req(adm,"POST","/api/auth/setup",{"api_key":"x","username":"admin","password":"password1"}).status_code==401,"setup wrong key")
ck(req(adm,"POST","/api/auth/setup",{"api_key":"testkey123","username":"admin","password":"password1"},h={}).status_code==403,"setup needs CSRF header")
r=req(adm,"POST","/api/auth/setup",{"api_key":"testkey123","username":"Admin","password":"password1"}); ck(r.status_code==200,"setup ok")
ck("HttpOnly" in r.headers.get("set-cookie","") and "Secure" not in r.headers.get("set-cookie",""),"cookie flags")
ck(req(adm,"POST","/api/auth/setup",{"api_key":"testkey123","username":"x2x","password":"password1"}).status_code==409,"setup once")
accs=adm.get(B+"/api/accounts").json()["accounts"]; admin_ids=[a["id"] for a in accs]
ck(sorted(admin_ids)==["main","second"] and all("owner_id" not in a and "owner_name" not in a for a in accs),"migration gives legacy accounts to first admin; no owner fields exposed")
ck(req(adm,"POST","/api/accounts",{"name":"Z"},h={}).status_code==403,"POST without CSRF 403")
ck(req(adm,"POST","/api/accounts",{"name":"Z"},h={**H,"Origin":"http://evil.example"}).status_code==403,"foreign Origin 403")

# ---- users
for u,p in (("alice","alicepass1"),("bob","bobpass123")):
    ck(req(adm,"POST","/api/users",{"username":u,"password":p,"role":"user"}).status_code==200,"create "+u)
users={u["username"]:u for u in adm.get(B+"/api/users").json()["users"]}
ck(users["alice"]["accounts"]==1 and set(users["alice"])=={"id","username","role","disabled","created_at","accounts"},"users list shows only counts")
A=login("alice","alicepass1"); Bs=login("bob","bobpass123")
aid=A.get(B+"/api/status").json()["accounts"][0]["id"]; bid=Bs.get(B+"/api/status").json()["accounts"][0]["id"]
# ---- admin cannot touch user accounts
for foreign in (aid,bid):
    q="?account="+foreign
    ck(adm.get(B+"/api/contacts"+q).status_code==404,"admin contacts GET 404")
    ck(req(adm,"POST","/api/contacts"+q,{"names":"x"}).status_code==404,"admin contacts POST 404")
    ck(req(adm,"PUT","/api/contacts/rename"+q,{"old":"a","new":"b"}).status_code==404,"admin rename contact 404")
    ck(req(adm,"DELETE","/api/contacts"+q+"&name=x").status_code==404,"admin delete contact 404")
    ck(adm.get(B+"/api/cookies"+q).status_code==404,"admin cookies GET 404")
    ck(req(adm,"PUT","/api/cookies"+q,{"raw":"a=b"}).status_code==404,"admin cookies PUT 404")
    ck(req(adm,"DELETE","/api/cookies"+q).status_code==404,"admin cookies DELETE 404")
    ck(req(adm,"PUT","/api/accounts/"+foreign,{"schedules":[]}).status_code==404,"admin schedules 404")
    ck(req(adm,"PUT","/api/accounts/"+foreign,{"name":"hack"}).status_code==404,"admin rename 404")
    ck(req(adm,"DELETE","/api/accounts/"+foreign).status_code==404,"admin delete account 404")
    ck(req(adm,"POST","/api/run",{"mode":"test","account":foreign}).status_code==404,"admin run 404")
    ck(req(adm,"POST","/api/login/start"+q).status_code==404,"admin login start 404")
ck(foreign not in [a["id"] for a in adm.get(B+"/api/accounts").json()["accounts"]] and set(a["id"] for a in adm.get(B+"/api/status").json()["accounts"])==set(admin_ids),"admin lists exclude user accounts")
ck(req(adm,"PUT","/api/accounts/"+admin_ids[0],{"name":"Utama Admin"}).status_code==200,"admin edits own account")
# ---- users cannot touch admin accounts or each other
for foreign in ("main","second",bid):
    ck(A.get(B+"/api/contacts?account="+foreign).status_code==404,"alice cannot read "+foreign)
# ---- history/proofs/screenshot scoping with real runs
os.makedirs(D+"/proofs/cccccccc",exist_ok=True)
ck(adm.get(B+"/api/proof/aaaaaaaa/1.jpg").status_code==200,"admin sees own seeded proof (main)")
ck(adm.get(B+"/api/proof/bbbbbbbb/1.jpg").status_code==200,"admin sees own seeded proof (second)")
ck(A.get(B+"/api/proof/aaaaaaaa/1.jpg").status_code==404,"alice cannot see admin proof")
ck(adm.get(B+"/api/run/screenshot").status_code==404,"admin screenshot of foreign/unknown account 404") if False else None
# screenshot owned by alice
json.dump({"account_id":aid},open(D+"/last_run.json","w"))
ck(adm.get(B+"/api/run/screenshot").status_code==404 and A.get(B+"/api/run/screenshot").status_code==200,"screenshot only for its owner (admin 404)")
json.dump({"account_id":"second"},open(D+"/last_run.json","w"))
ck(adm.get(B+"/api/run/screenshot").status_code==200 and A.get(B+"/api/run/screenshot").status_code==404,"admin own screenshot ok, alice 404")
# alice run -> queue isolation for admin
r=req(A,"POST","/api/run",{"mode":"check","account":aid}); ck(r.status_code==200 and r.json()["job"]["kind"]=="check","alice enqueues run: "+r.text[:100])
ck(req(A,"POST","/api/run",{"mode":"check","account":aid}).status_code==409,"duplicate (account,kind) rejected")
st=adm.get(B+"/api/status").json(); cur=adm.get(B+"/api/run/current").json()
ck(st["queue"]["mine"]==[] and not st["running"] and st["current"] is None and cur["run"] is None,"admin sees no details of alice's job")
ck(set(st["queue"])=={"mine","queued","running","workers"} and st["queue"]["queued"]+st["queue"]["running"]>=1,"admin sees only aggregate counts "+json.dumps(st["queue"]))
ck(not any(k in json.dumps(adm.get(B+"/api/queue").json()) for k in (aid,"alice")),"queue endpoint leaks no names/ids")
sa=A.get(B+"/api/status").json(); ck(len(sa["queue"]["mine"])==1 and sa["queue"]["mine"][0]["account_id"]==aid,"alice sees her own job")
ck(req(adm,"POST","/api/run/stop").json()["stopped"]==0,"admin stop affects nothing of alice")
jid=sa["queue"]["mine"][0]["id"]; ck(req(adm,"DELETE","/api/jobs/"+jid).status_code==404,"admin cannot cancel alice's job")
idle(A)
ck(all(r["account"]["id"] in admin_ids for r in adm.get(B+"/api/history").json()["items"]),"admin history only own accounts")
ah=A.get(B+"/api/history").json()["items"]; ck(len(ah)==1 and ah[0]["by"]=="alice","alice history only her run")
ck(A.get(B+"/api/dashboard?account=main").status_code==404 and A.get(B+"/api/history?account=main").status_code==404,"alice cannot read admin dashboard/history by account id")
ck(adm.get(B+"/api/proof/"+ah[0]["id"]+"/1.jpg").status_code==404,"admin cannot fetch alice's proof")
r=req(adm,"POST","/api/run",{"mode":"check","account":admin_ids[0]}); ck(r.status_code==200,"admin run ok")
st=A.get(B+"/api/status").json(); ck(st["queue"]["mine"]==[] and st["current"] is None,"alice sees nothing of admin's job")
idle(adm)
req(adm,"DELETE","/api/history"); ck(adm.get(B+"/api/history").json()["items"]==[] and len(A.get(B+"/api/history").json()["items"])==1,"admin clear history only own")
# ---- remote login owner only
r=req(A,"POST","/api/login/start?account="+aid); ck(r.status_code==200,"alice starts remote login "+r.text[:60])
for p,m,want in (("/api/login/status","GET",200),("/api/login/frame","GET",204),("/api/login/input","POST",400),("/api/login/save","POST",400),("/api/login/stop","POST",200)):
    r=req(adm,m,p,{"type":"click"} if m=="POST" else None); ck(r.status_code==want and (p!="/api/login/status" or r.json()=={"active":False}),f"admin {m} {p} sees no session of alice -> {r.status_code}")
ck(adm.get(B+"/api/status").json()["login"] is None,"admin status hides login")
ck(A.get(B+"/api/login/frame").status_code==200,"alice sees own frame")
ck(req(A,"POST","/api/login/stop").status_code==200,"alice stops login")
# ---- api key = oldest admin, own accounts only
r=requests.get(B+"/api/accounts",headers=KEY).json()["accounts"]; ck(sorted(a["id"] for a in r)==sorted(admin_ids),"api key sees only oldest admin's accounts")
ck(requests.get(B+"/api/contacts?account="+aid,headers=KEY).status_code==404,"api key 404 on user account")
r=requests.post(B+"/api/accounts",json={"name":"ViaKey"},headers=KEY); ck(r.status_code==200 and requests.get(B+"/api/accounts",headers=KEY).json()["accounts"][-1]["name"]=="ViaKey","api key creates under oldest admin")
kid=[a["id"] for a in adm.get(B+"/api/accounts").json()["accounts"] if a["name"]=="ViaKey"]; ck(len(kid)==1,"admin sees key-created account")
req(adm,"DELETE","/api/accounts/"+kid[0])
# promote bob: oldest admin remains api key identity
ck(req(adm,"PUT","/api/users/"+users["bob"]["id"],{"role":"admin"}).status_code==200,"promote bob")
Bs=login("bob","bobpass123"); ck(Bs.get(B+"/api/users").status_code==200,"bob admin")
ck([a["id"] for a in Bs.get(B+"/api/accounts").json()["accounts"]]==[bid],"promoted bob still only sees own account")
ck(sorted(a["id"] for a in requests.get(B+"/api/accounts",headers=KEY).json()["accounts"])==sorted(admin_ids),"api key still oldest admin")
ck(Bs.get(B+"/api/contacts?account=main").status_code==404,"second admin cannot read first admin's account")
ck(req(Bs,"PUT","/api/users/"+users["bob"]["id"],{"role":"user"}).status_code==400,"bob last? no: two admins -> allowed demote check")if False else None
ck(req(adm,"PUT","/api/users/"+users["bob"]["id"],{"role":"user"}).status_code==200,"demote bob again")
# caps (global cap 10 also applies)
for i in range(12): req(adm,"POST","/api/accounts",{"name":f"Cap{i}"})
ck(len(adm.get(B+"/api/accounts").json()["accounts"])==10 and req(adm,"POST","/api/accounts",{"name":"CapX"}).status_code==400,"admin per-owner cap 10")
for a in adm.get(B+"/api/accounts").json()["accounts"]:
    if a["name"].startswith("Cap"): req(adm,"DELETE","/api/accounts/"+a["id"])
for i in range(4): req(A,"POST","/api/accounts",{"name":f"N{i}"})
ck(req(A,"POST","/api/accounts",{"name":"Sixth"}).status_code==400,"user cap 5")
for a in A.get(B+"/api/accounts").json()["accounts"]:
    if a["name"].startswith("N"): req(A,"DELETE","/api/accounts/"+a["id"])
# last-admin protections
aduid=adm.get(B+"/api/auth/state").json()["user"]["id"]
ck(req(adm,"PUT","/api/users/"+aduid,{"role":"user"}).status_code==400,"cannot demote last admin")
ck(req(adm,"PUT","/api/users/"+aduid,{"disabled":True}).status_code==400,"cannot disable last admin")
ck(req(adm,"DELETE","/api/users/"+aduid).status_code==400,"cannot delete self / last admin")
# password change + sessions
A2=login("alice","alicepass1")
ck(req(A,"POST","/api/auth/password",{"current":"alicepass1","new":"newpass123"}).status_code==200,"pw change")
ck(A.get(B+"/api/status").status_code==200 and A2.get(B+"/api/status").status_code==401,"other sessions killed, current kept")
# disable / enable
uid=users["alice"]["id"]
ck(req(adm,"PUT","/api/users/"+uid,{"disabled":True}).status_code==200 and A.get(B+"/api/status").status_code==401,"disable kills session")
ck(req(S(),"POST","/api/auth/login",{"username":"alice","password":"newpass123"}).status_code==401,"disabled cannot login")
ck(req(adm,"PUT","/api/users/"+uid,{"disabled":False,"password":"resetpass1"}).status_code==200,"enable + reset")
A=login("alice","resetpass1")
# ---- delete user deletes accounts + data
aids=[a["id"] for a in A.get(B+"/api/accounts").json()["accounts"]]
for x in aids: os.makedirs(f"{D}/accounts/{x}",exist_ok=True)
r=req(A,"POST","/api/run",{"mode":"check","account":aids[0]}); idle(A)
runid=A.get(B+"/api/history").json()["items"][0]["id"]; os.makedirs(f"{D}/proofs/{runid}",exist_ok=True); open(f"{D}/proofs/{runid}/1.jpg","wb").write(b"x")
before=[a["id"] for a in adm.get(B+"/api/accounts").json()["accounts"]]
r=req(adm,"DELETE","/api/users/"+uid); ck(r.status_code==200 and r.json()["deleted_accounts"]==len(aids),"delete user -> "+r.text)
ck(all(not os.path.exists(f"{D}/accounts/{x}") for x in aids),"account dirs removed")
ck(not os.path.exists(f"{D}/proofs/{runid}"),"proofs removed")
ck(sqlite3.connect(D+'/streak.db').execute('select count(*) from runs where id=?',(runid,)).fetchone()[0]==0,"history purged")
ck([a["id"] for a in adm.get(B+"/api/accounts").json()["accounts"]]==before,"admin accounts untouched (nothing reassigned)")
ck(A.get(B+"/api/status").status_code==401,"deleted user's session dead")
ck(req(adm,"DELETE","/api/users/zzzz").status_code==404,"delete unknown 404")
ck(req(Bs,"POST","/api/auth/logout").status_code==200 and Bs.get(B+"/api/status").status_code==401,"logout")
ck(requests.get(B+"/api/status",headers={"X-API-Key":"wrong"}).status_code==401,"wrong key 401")
print("FAILS",fails)

# ---- paginasi riwayat
h=adm.get(B+"/api/history?page=1&page_size=10").json(); ck(set(h)=={"items","total","page","page_size"} and h["page_size"]==10,"history shape")
ck(adm.get(B+"/api/history?page_size=7").status_code==400,"page_size must be 10/20/50")
ck(adm.get(B+"/api/history?status=bogus").status_code==400 and adm.get(B+"/api/history?mode=bogus").status_code==400,"bad filters rejected")
ck(adm.get(B+"/api/history?account=zzz").status_code in (403,404),"foreign account history refused")
d=adm.get(B+"/api/dashboard?account=main").json(); ck(set(d)>={"today","runs_today","send_days","week"},"dashboard endpoint")
import sys as _sys
_sys.exit(1 if fails else 0)
