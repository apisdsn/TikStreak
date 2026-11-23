import os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests, time
import os
B=os.environ.get("BARA_BASE","http://127.0.0.1:8791"); H={"X-Requested-With":"bara"}
def S(): return requests.Session()
adm=S(); r=adm.post(B+"/api/auth/setup",json={"api_key":"testkey123","username":"admin","password":"password1"},headers=H)
for u in ("alice","bob"): adm.post(B+"/api/users",json={"username":u,"password":u+"pass123","role":"user"},headers=H)
A=S(); A.post(B+"/api/auth/login",json={"username":"alice","password":"alicepass123"},headers=H)
Bo=S(); Bo.post(B+"/api/auth/login",json={"username":"bob","password":"bobpass123"},headers=H)
fails=[]
def ck(c,m):
    print(("ok   " if c else "FAIL ")+m); (not c) and fails.append(m)
r=A.post(B+"/api/login/start",headers=H); ck(r.status_code==200,"alice starts login session")
r=Bo.post(B+"/api/login/start",headers=H); ck(r.status_code==400 and "Sedang Dipakai" in r.json()["detail"],"bob blocked by LOGIN_SESSIONS=1: "+r.text)
ck(Bo.get(B+"/api/login/status").json()=={"active":False},"bob sees no session")
ck(A.get(B+"/api/login/status").json()["active"],"alice session untouched")
aid=A.get(B+"/api/status").json()["accounts"][0]["id"]
r=A.post(B+"/api/run",json={"mode":"check","account":aid},headers=H); ck(r.status_code==409,"run on account with active login -> 409")
A.post(B+"/api/login/stop",headers=H)
r=Bo.post(B+"/api/login/start",headers=H); ck(r.status_code==200,"bob can start after alice stops")
Bo.post(B+"/api/login/stop",headers=H)
print("FAILS",fails)
import sys as _sys
_sys.exit(1 if fails else 0)
