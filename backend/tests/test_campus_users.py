import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from flask import Flask

from api.campus_account import configure_accounts
from api.campus_reports import configure_reports
from api.campus_users import configure_users


class CampusUsersTests(unittest.TestCase):
    origin = "http://127.0.0.1:5173"
    prefix = "/api/campus"

    def setUp(self):
        folder = self.enterContext(tempfile.TemporaryDirectory())
        app = Flask(__name__)
        with patch.dict(os.environ, {
            "CAMPUS_ORIGIN": self.origin, "CAMPUS_SESSION_SECRET": "test-secret",
            "CAMPUS_GOOGLE_CLIENT_ID": "test-id", "CAMPUS_GOOGLE_CLIENT_SECRET": "test-secret",
        }):
            configure_accounts(app)
        configure_reports(app)
        configure_users(app)
        app.config.update(TESTING=True, CAMPUS_PREVIEW=False,
                          CAMPUS_REPORTS_FILE=os.path.join(folder, "reports.json"),
                          CAMPUS_USERS_DB=os.path.join(folder, "users.sqlite3"))
        self.app = app
        self.owner = app.test_client()
        self.member = app.test_client()

    def login(self, client, subject, email, verified=True):
        oauth = Mock()
        oauth.authorize_access_token.return_value = {"userinfo": {
            "sub": subject, "name": subject, "email": email, "email_verified": verified,
        }}
        with patch.object(self.app.extensions["campus_oauth"], "create_client", return_value=oauth):
            self.assertEqual(client.get(self.prefix + "/callback/google").status_code, 302)
        return client.get(self.prefix + "/session").json

    def headers(self, client):
        return {"Origin": self.origin, "X-Campus-CSRF": client.get(self.prefix + "/session").json["csrf"]}

    def test_login_list_role_change_and_immediate_revocation(self):
        url = self.prefix + "/admin/users"
        self.assertEqual(self.owner.get(url).status_code, 401)
        self.assertTrue(self.login(self.owner, "owner-id", "yuhsin099@gmail.com")["account"]["admin"])
        self.assertFalse(self.login(self.member, "member-id", "member@gmail.com")["account"]["admin"])
        self.assertEqual(self.member.get(url).status_code, 403)
        rows = self.owner.get(url).json["users"]
        self.assertEqual({row["subject"] for row in rows}, {"owner-id", "member-id"})
        self.assertEqual(next(row for row in rows if row["owner"])["role"], "admin")
        target = url + "/google/member-id"
        self.assertEqual(self.owner.patch(target, json={"role": "admin", "previous_role": "user"}).status_code, 403)
        self.assertEqual(self.owner.patch(target, headers=self.headers(self.owner), json={
            "role": "admin", "previous_role": "user",
        }).status_code, 200)
        self.assertEqual(self.member.patch(target, headers=self.headers(self.member), json={
            "role": "admin", "previous_role": "admin",
        }).status_code, 200)
        self.assertTrue(self.member.get(self.prefix + "/session").json["account"]["admin"])
        self.assertEqual(self.member.get(url).status_code, 200)
        self.assertEqual(self.owner.patch(target, headers=self.headers(self.owner), json={
            "role": "user", "previous_role": "user",
        }).status_code, 409)
        self.assertEqual(self.owner.patch(target, headers=self.headers(self.owner), json={
            "role": "user", "previous_role": "admin",
        }).status_code, 200)
        self.assertFalse(self.member.get(self.prefix + "/session").json["account"]["admin"])
        self.assertEqual(self.member.get(url).status_code, 403)
        self.assertEqual(self.member.get(self.prefix + "/admin/reports").status_code, 403)
        self.assertEqual(self.member.patch(target, headers=self.headers(self.member), json={
            "role": "admin", "previous_role": "user",
        }).status_code, 403)

    def test_owner_cannot_be_demoted_and_unverified_email_cannot_bootstrap(self):
        self.login(self.owner, "owner-id", "yuhsin099@gmail.com", verified=False)
        self.assertEqual(self.owner.get(self.prefix + "/admin/users").status_code, 403)
        self.login(self.owner, "owner-id", "yuhsin099@gmail.com")
        response = self.owner.patch(self.prefix + "/admin/users/google/owner-id",
                                    headers=self.headers(self.owner), json={
                                        "role": "user", "previous_role": "admin",
                                    })
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.owner.get(self.prefix + "/session").json["account"]["admin"])
        self.login(self.owner, "owner-id", "other@gmail.com")
        self.assertFalse(self.owner.get(self.prefix + "/session").json["account"]["admin"])

    def test_invalid_and_unknown_updates_leave_roles_intact(self):
        self.login(self.owner, "owner-id", "yuhsin099@gmail.com")
        self.login(self.member, "member-id", "member@gmail.com")
        url = self.prefix + "/admin/users/google/member-id"
        headers = self.headers(self.owner)
        self.assertEqual(self.owner.patch(url, headers=headers, json={"role": "owner"}).status_code, 400)
        self.assertEqual(self.owner.patch(self.prefix + "/admin/users/google/missing",
                                          headers=headers, json={"role": "admin", "previous_role": "user"}).status_code, 404)
        self.assertFalse(self.member.get(self.prefix + "/session").json["account"]["admin"])

    def test_owner_email_cannot_be_assigned_to_another_subject(self):
        self.login(self.owner, "owner-id", "yuhsin099@gmail.com")
        oauth = Mock()
        oauth.authorize_access_token.return_value = {"userinfo": {
            "sub": "different-id", "name": "Different", "email": "yuhsin099@gmail.com",
            "email_verified": True,
        }}
        with patch.object(self.app.extensions["campus_oauth"], "create_client", return_value=oauth):
            response = self.member.get(self.prefix + "/callback/google")
        self.assertEqual(response.location, self.origin + "/campus?login=failed")
        self.assertIsNone(self.member.get(self.prefix + "/session").json["account"])


if __name__ == "__main__":
    unittest.main()