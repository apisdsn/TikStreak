import os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests, os
import os
B=os.environ.get("BARA_BASE","http://127.0.0.1:8791"); H={"X-Requested-With":"streak-panel"}; D=os.environ.get("BARA_DATA","")
s=requests.Session(); s.post(B+"/api/auth/setup",json={"api_key":"testkey123","username":"admin","password":"password1"},headers=H)
fails=[]
def ck(c,m):
    print(("ok   " if c else "FAIL ")+m); (not c) and fails.append(m)
ck(s.put(B+"/api/cookies?account=main",json={"raw":"sessionid=ENCCOOKIEVALUE123; other=ENCOTHERVAL"},headers=H).status_code==200,"cookie saved")
ck(s.put(B+"/api/me/notifications",json={"discord_webhook":"https://discord.com/api/webhooks/5/ENCUSERHOOK","telegram_token":"ENCUSERTOKEN987","telegram_chat_id":"42"},headers=H).status_code==200,"user notify saved")
ck(s.put(B+"/api/settings",json={"discord_webhook":"https://discord.com/api/webhooks/6/ENCGLOBALHOOK","telegram_token":"ENCGLOBALTOKEN654"},headers=H).status_code==200,"global notify saved")
c=s.get(B+"/api/cookies?account=main").json(); ck(c["present"] and c["has_session"] and c["count"]==2,"cookie summary still readable "+str(c))
n=s.get(B+"/api/me/notifications").json(); ck(n["discord_webhook_set"] and n["telegram_token_set"] and "discord_webhook" not in n,"masked notify")
g=s.get(B+"/api/settings").json(); ck(g["discord_webhook_set"] and "discord_webhook" not in g,"masked global")
raw=b""
for f in os.listdir(D):
    if f.startswith("streak.db"): raw+=open(os.path.join(D,f),"rb").read()
for nd in (b"ENCCOOKIEVALUE123",b"ENCOTHERVAL",b"ENCUSERHOOK",b"ENCUSERTOKEN987",b"ENCGLOBALHOOK",b"ENCGLOBALTOKEN654"):
    ck(nd not in raw,"raw db (incl. WAL) has no "+nd.decode())
print("FAILS",fails)
import sys as _sys
_sys.exit(1 if fails else 0)
