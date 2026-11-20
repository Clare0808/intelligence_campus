import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import app


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


if __name__ == "__main__":
    unittest.main()