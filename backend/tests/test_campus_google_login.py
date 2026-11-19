import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from flask import Flask

from api.campus_account import configure_accounts
from api.campus_reports import configure_reports
from api.campus_users import configure_users


class GoogleLoginTests(unittest.TestCase):
    origin = "http://127.0.0.1:5173"
    prefix = "/api/campus"

    def setUp(self):
        folder = self.enterContext(tempfile.TemporaryDirectory())
        app = Flask(__name__)
        with patch.dict(os.environ, {
            "CAMPUS_ORIGIN": self.origin,
            "CAMPUS_SESSION_SECRET": "test-session-secret",
            "CAMPUS_GOOGLE_CLIENT_ID": "test-client-id",
            "CAMPUS_GOOGLE_CLIENT_SECRET": "test-client-secret",
            "CAMPUS_ADMINS": "google:approved-admin",
            "CAMPUS_PORTAL_CLIENT_ID": "",
            "CAMPUS_PORTAL_CLIENT_SECRET": "",
        }):
            configure_accounts(app)
        configure_reports(app)
        configure_users(app)
        app.config.update(
            TESTING=True, CAMPUS_PREVIEW=True,
            CAMPUS_REPORTS_FILE=os.path.join(folder, "reports.json"),
            CAMPUS_USERS_DB=os.path.join(folder, "users.sqlite3"),
        )
        self.app = app
        self.client = app.test_client()

    def test_provider_is_available_in_preview_and_uses_frontend_callback(self):
        providers = self.client.get(self.prefix + "/session").json["providers"]
        self.assertTrue(next(item for item in providers if item["id"] == "google")["enabled"])
        self.assertFalse(next(item for item in providers if item["id"] == "portal")["enabled"])

        oauth_client = Mock()
        oauth_client.authorize_redirect.return_value = "google-authorization-response"
        with patch.object(self.app.extensions["campus_oauth"], "create_client", return_value=oauth_client):
            response = self.client.get(self.prefix + "/login/google")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "google-authorization-response")
        oauth_client.authorize_redirect.assert_called_once_with(
            self.origin + self.prefix + "/callback/google"
        )

    def test_verified_subject_signs_in_without_granting_admin_automatically(self):
        oauth_client = Mock()
        oauth_client.authorize_access_token.return_value = {
            "userinfo": {"sub": "google-user-123", "name": "Google User"}
        }
        with patch.object(self.app.extensions["campus_oauth"], "create_client", return_value=oauth_client):
            response = self.client.get(self.prefix + "/callback/google")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, self.origin + "/campus?login=success")
        account = self.client.get(self.prefix + "/session").json["account"]
        self.assertEqual(account["provider"], "google")
        self.assertEqual(account["subject"], "google-user-123")
        self.assertEqual(account["name"], "Google User")
        self.assertFalse(account["admin"])

    def test_only_verified_named_google_email_starts_as_admin(self):
        endpoint = self.prefix + "/admin/reports"
        self.assertEqual(self.client.get(endpoint).status_code, 401)
        oauth_client = Mock()
        claims = {"sub": "google-user-123", "name": "Google User"}
        oauth_client.authorize_access_token.return_value = {"userinfo": claims}
        with patch.object(self.app.extensions["campus_oauth"], "create_client", return_value=oauth_client):
            for email, verified, allowed in (
                ("other@gmail.com", True, False),
                ("yuhsin099@gmail.com", False, False),
                ("yuhsin099@gmail.com", "true", False),
                ("Yuhsin099@Gmail.com", True, True),
            ):
                claims.update(email=email, email_verified=verified)
                self.client.get(self.prefix + "/callback/google")
                account = self.client.get(self.prefix + "/session").json["account"]
                self.assertEqual(account["admin"], allowed)
                self.assertEqual(self.client.get(endpoint).status_code, 200 if allowed else 403)

        with self.client.session_transaction() as cookie:
            account = cookie["campus_account"]
            cookie["campus_account"] = {**account, "provider": "portal"}
        self.assertFalse(self.client.get(self.prefix + "/session").json["account"]["admin"])
        self.assertEqual(self.client.get(endpoint).status_code, 403)

    def test_legacy_admin_subject_does_not_grant_access(self):
        with self.client.session_transaction() as cookie:
            cookie["campus_account"] = {
                "provider": "google", "subject": "approved-admin", "name": "Legacy Admin",
            }
        self.assertFalse(self.client.get(self.prefix + "/session").json["account"]["admin"])
        self.assertEqual(self.client.get(self.prefix + "/admin/reports").status_code, 403)

    def test_missing_subject_and_provider_error_do_not_sign_in(self):
        oauth_client = Mock()
        oauth_client.authorize_access_token.return_value = {"userinfo": {"name": "No subject"}}
        with patch.object(self.app.extensions["campus_oauth"], "create_client", return_value=oauth_client):
            response = self.client.get(self.prefix + "/callback/google")
        self.assertEqual(response.location, self.origin + "/campus?login=failed")
        self.assertIsNone(self.client.get(self.prefix + "/session").json["account"])

        oauth_client.authorize_access_token.side_effect = ValueError("OAuth state mismatch")
        with patch.object(self.app.extensions["campus_oauth"], "create_client", return_value=oauth_client):
            response = self.client.get(self.prefix + "/callback/google")
        self.assertEqual(response.location, self.origin + "/campus?login=failed")
        self.assertIsNone(self.client.get(self.prefix + "/session").json["account"])

    def test_unconfigured_provider_returns_to_frontend(self):
        response = self.client.get(self.prefix + "/login/portal")
        self.assertEqual(response.location, self.origin + "/campus?login=unavailable")


if __name__ == "__main__":
    unittest.main()