import sys, tempfile, unittest
import os
from unittest.mock import patch
from pathlib import Path
from flask import Flask
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"backend"))
import account_settings as a

class AccountsTest(unittest.TestCase):
 @patch.dict(os.environ, {"GATEWAY_ADMIN_PASSWORD": "test-initial-admin-123"})
 def test_lifecycle(self):
  with tempfile.TemporaryDirectory() as d:
   old=a.DB
   a.DB=Path(d)/"accounts.sqlite3"
   try:
    app=Flask(__name__);app.secret_key="test-only";app.register_blueprint(a.bp)
    c=app.test_client()
    self.assertEqual(c.get("/api/accounts").status_code,401)
    with c.session_transaction() as s: s["account_csrf"]="token"
    h={"X-CSRF-Token":"token"}
    self.assertEqual(c.post("/api/accounts/sign-in",json={"username":"admin","password":"bad"},headers=h).status_code,401)
    data=c.post("/api/accounts/sign-in",json={"username":"admin","password":"test-initial-admin-123"},headers=h).get_json()
    h={"X-CSRF-Token":data["csrf"]}
    self.assertEqual(c.post("/api/accounts",json={}).status_code,403)
    payload={"username":"testuser","name":"Test User","role":"user","password":"long-password-123"}
    self.assertEqual(c.post("/api/accounts",json=payload,headers=h).status_code,200)
    self.assertEqual(c.post("/api/accounts",json=payload,headers=h).status_code,409)
    rows=c.get("/api/accounts").get_json()["accounts"];user=next(x for x in rows if x["username"]=="testuser")
    self.assertNotIn("password_hash",user)
    u=app.test_client()
    with u.session_transaction() as s: s["account_csrf"]="u"
    ud=u.post("/api/accounts/sign-in",json={"username":"testuser","password":"long-password-123"},headers={"X-CSRF-Token":"u"}).get_json()
    uh={"X-CSRF-Token":ud["csrf"]}
    self.assertEqual(u.post("/api/accounts",json=payload,headers=uh).status_code,403)
    self.assertEqual(u.patch("/api/accounts/"+str(user["id"]),json={"role":"creator"},headers=uh).status_code,403)
    self.assertEqual(u.patch("/api/accounts/"+str(user["id"]),json={"current_password":"long-password-123","password":"changed-password-123"},headers=uh).status_code,200)
    self.assertEqual(c.patch("/api/accounts/1",json={"role":"user"},headers=h).status_code,400)
    self.assertEqual(c.delete("/api/accounts/"+str(user["id"]),headers=h).status_code,200)
    self.assertEqual(u.get("/api/accounts").status_code,401)
   finally:a.DB=old
if __name__=="__main__":unittest.main()
