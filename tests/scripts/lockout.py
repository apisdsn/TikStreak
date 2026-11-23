import os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import os
B=os.environ.get("BARA_BASE","http://127.0.0.1:8791"); H={"X-Requested-With":"streak-panel"}
codes=[requests.post(B+"/api/auth/login",json={"username":"bob","password":"bad%d"%i},headers=H).status_code for i in range(7)]
print(codes)
r=requests.post(B+"/api/auth/login",json={"username":"bob","password":"bobpass123"},headers=H); print(r.status_code,r.json())
assert codes[:5]==[401]*5 and codes[5]==429 and r.status_code==429
print("lockout ok")
