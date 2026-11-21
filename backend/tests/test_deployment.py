import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app import app
from api import construction


class DeploymentTests(unittest.TestCase):
    def test_frontend_routes_and_missing_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory)
            (dist / "index.html").write_text("<h1>campus</h1>", encoding="utf-8")
            (dist / "assets").mkdir()
            (dist / "assets" / "app.js").write_text("// bundled", encoding="utf-8")
            with patch("app.frontend_dist", dist):
                client = app.test_client()
                for route in ("/", "/campus", "/campus/admin", "/map"):
                    with self.subTest(route=route):
                        response = client.get(route)
                        self.assertIn(b"campus", response.get_data())
                        response.close()
                response = client.get("/assets/app.js")
                self.assertIn(b"bundled", response.get_data())
                response.close()
                self.assertEqual(client.get("/assets/missing.js").status_code, 404)
                self.assertEqual(client.get("/api/missing").status_code, 404)
                self.assertEqual(client.get("/health").json, {"status": "ok"})

    def test_public_site_disables_unauthenticated_ai_refresh(self):
        with patch.dict(app.config, {"CAMPUS_ORIGIN": "https://campus.example.com"}):
            self.assertEqual(app.test_client().post("/api/construction/refresh").status_code, 403)

    def test_official_refresh_requires_admin_and_valid_csrf(self):
        feed = SimpleNamespace(refresh=lambda: 2)
        with patch.dict(app.config, {"CAMPUS_ORIGIN": "https://campus.example.com"}), patch.dict(
            app.extensions, {"construction_feed": feed}
        ), patch("api.campus_account.user_role", return_value="reporter"):
            client = app.test_client()
            endpoint = "/api/construction/refresh-official"
            self.assertEqual(client.post(endpoint).status_code, 401)
            client.get("/api/campus/session")
            with client.session_transaction() as session:
                session["campus_account"] = {"provider": "google", "subject": "user", "name": "User"}
                session["campus_csrf"] = "valid-token"
            headers = {"Origin": "https://campus.example.com", "X-Campus-CSRF": "valid-token"}
            self.assertEqual(client.post(endpoint, headers=headers).status_code, 403)

        with patch.dict(app.config, {"CAMPUS_ORIGIN": "https://campus.example.com"}), patch.dict(
            app.extensions, {"construction_feed": feed}
        ), patch("api.campus_account.user_role", return_value="admin"):
            self.assertEqual(client.post(endpoint).status_code, 403)
            self.assertEqual(client.post(endpoint, headers={
                "Origin": "https://other.example.com", "X-Campus-CSRF": "valid-token"
            }).status_code, 403)
            self.assertEqual(client.post(endpoint, headers=headers).json["count"], 2)

    def test_official_refresh_handles_unavailable_feed_conflict_and_failures(self):
        client = app.test_client()
        endpoint = "/api/construction/refresh-official"
        with client.session_transaction() as session:
            session["campus_account"] = {"provider": "google", "subject": "user", "name": "User"}
            session["campus_csrf"] = "valid-token"
        headers = {"Origin": "https://campus.example.com", "X-Campus-CSRF": "valid-token"}
        with patch.dict(app.config, {"CAMPUS_ORIGIN": "https://campus.example.com"}), patch(
            "api.campus_account.user_role", return_value="admin"
        ):
            with patch.dict(app.extensions, clear=True):
                self.assertEqual(client.post(endpoint, headers=headers).status_code, 503)
            feed = SimpleNamespace(refresh=lambda: 1)
            with patch.dict(app.extensions, {"construction_feed": feed}):
                construction.refresh_lock.acquire()
                try:
                    self.assertEqual(client.post(endpoint, headers=headers).status_code, 409)
                finally:
                    construction.refresh_lock.release()
            def fail():
                raise RuntimeError("private source details")
            with patch.dict(app.extensions, {"construction_feed": SimpleNamespace(refresh=fail)}):
                response = client.post(endpoint, headers=headers)
                self.assertEqual(response.status_code, 502)
                self.assertNotIn("private source details", response.json["message"])
                self.assertFalse(construction.refresh_lock.locked())


if __name__ == "__main__":
    unittest.main()