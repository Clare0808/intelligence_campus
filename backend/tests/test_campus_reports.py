import tempfile
import sqlite3
from contextlib import closing
import unittest
from io import BytesIO
from pathlib import Path

from flask import Flask
from openpyxl import load_workbook

from api.campus_account import configure_accounts
from api.campus_reports import configure_reports, database


class CampusReportsTests(unittest.TestCase):
    origin = "http://127.0.0.1:5173"
    prefix = "/api/campus"

    def setUp(self):
        folder = self.enterContext(tempfile.TemporaryDirectory())
        app = Flask(__name__)
        configure_accounts(app)
        configure_reports(app)
        app.config.update(
            TESTING=True, CAMPUS_PREVIEW=True, CAMPUS_ORIGIN=self.origin,
            CAMPUS_REPORTS_DB=str(Path(folder) / "reports.sqlite3"),
        )
        self.app = app

    def sign_in(self, client, role):
        response = client.get(self.prefix + "/session")
        headers = {"Origin": self.origin, "X-Campus-CSRF": response.json["csrf"]}
        response = client.post(self.prefix + "/session/preview", json={"role": role}, headers=headers)
        self.assertEqual(response.status_code, 200)
        return {**headers, "X-Campus-CSRF": response.json["csrf"]}

    def test_review_and_export_keep_pending_reports_private_and_cells_as_text(self):
        reporter = self.app.test_client()
        admin = self.app.test_client()
        reporter_headers = self.sign_in(reporter, "reporter")
        draft = {
            "kind": "idle", "title": "=1+2", "details": "Test fixture",
            "longitude": 121.1945, "latitude": 24.968189,
        }

        created = reporter.post(self.prefix + "/reports", json=draft, headers=reporter_headers)
        self.assertEqual(created.status_code, 201)
        self.assertEqual(reporter.get(self.prefix + "/reports/map").json["reports"], [])
        self.assertEqual(reporter.get(self.prefix + "/admin/reports.xlsx").status_code, 403)

        admin_headers = self.sign_in(admin, "reviewer")
        path = self.prefix + f"/admin/reports/{created.json['id']}"
        self.assertEqual(admin.patch(path, json={
            "status": "approved", "previous_status": "pending",
        }, headers=admin_headers).status_code, 200)
        self.assertEqual(admin.patch(path, json={
            "status": "rejected", "previous_status": "pending",
        }, headers=admin_headers).status_code, 409)

        [published] = reporter.get(self.prefix + "/reports/map").json["reports"]
        self.assertNotIn("reporter", published)
        self.assertNotIn("reviewer", published)
        self.assertTrue(published["reviewed_at"])

        response = admin.get(self.prefix + "/admin/reports.xlsx")
        self.assertEqual(response.status_code, 200)
        book = load_workbook(BytesIO(response.data))
        self.assertEqual(book.active["C2"].value, draft["title"])
        self.assertEqual(book.active["C2"].data_type, "s")

    def test_sign_in_requires_preview_and_a_matching_origin(self):
        client = self.app.test_client()
        session = client.get(self.prefix + "/session").json
        headers = {"X-Campus-CSRF": session["csrf"], "Origin": "https://example.com"}
        endpoint = self.prefix + "/session/preview"
        self.assertEqual(client.post(endpoint, json={"role": "reviewer"}, headers=headers).status_code, 403)
        self.app.config["CAMPUS_PREVIEW"] = False
        headers["Origin"] = self.origin
        self.assertEqual(client.post(endpoint, json={"role": "reviewer"}, headers=headers).status_code, 403)

    def test_delete_removes_database_rows_and_does_not_reuse_report_id(self):
        reporter = self.app.test_client()
        headers = self.sign_in(reporter, "reporter")
        result = reporter.post(self.prefix + "/reports", json={
            "kind": "construction", "title": "Closed road fixture", "details": "Test fixture",
            "longitude": 121.1945, "latitude": 24.968189, "road_closed": True,
        }, headers=headers)
        path = self.prefix + f"/admin/reports/{result.json['id']}"
        self.assertEqual(reporter.delete(path, json={"previous_status": "pending"}, headers=headers).status_code, 403)
        admin = self.app.test_client()
        headers = self.sign_in(admin, "reviewer")
        self.assertEqual(admin.patch(path, json={
            "status": "approved", "previous_status": "pending",
        }, headers=headers).status_code, 200)
        self.assertEqual(len(reporter.get(self.prefix + "/reports/map").json["reports"]), 1)
        self.assertEqual(admin.delete(path, json={"previous_status": "approved"}).status_code, 403)
        self.assertEqual(admin.delete(path, json={"previous_status": "pending"}, headers=headers).status_code, 409)
        self.assertEqual(admin.delete(path, json={"previous_status": "approved"}, headers=headers).status_code, 200)
        self.assertEqual(reporter.get(self.prefix + "/reports/map").json["reports"], [])
        book = load_workbook(BytesIO(admin.get(self.prefix + "/admin/reports.xlsx").data))
        self.assertEqual(book.active.max_row, 1)
        self.assertEqual(admin.get(self.prefix + "/admin/reports").json["reports"], [])
        with self.app.app_context(), database() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM reports").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM report_deletions").fetchone()[0], 0)
        self.assertEqual(admin.patch(path, json={
            "status": "rejected", "previous_status": "approved",
        }, headers=headers).status_code, 409)
        self.assertEqual(admin.post(path + "/restore", headers=headers).status_code, 404)
        self.assertEqual(admin.delete(path, json={"previous_status": "approved"}, headers=headers).status_code, 409)
        created = reporter.post(self.prefix + "/reports", json={
            "kind": "damage", "title": "New report", "details": "Test fixture",
            "longitude": 121.1945, "latitude": 24.968189,
        }, headers=self.sign_in(reporter, "reporter"))
        self.assertGreater(created.json["id"], result.json["id"])
        self.assertEqual(admin.delete(path, json={"previous_status": "pending"}, headers=headers).status_code, 409)

    def test_old_database_and_previously_deleted_reports_can_be_permanently_deleted(self):
        with closing(sqlite3.connect(self.app.config["CAMPUS_REPORTS_DB"])) as connection, connection:
            connection.execute("""
                CREATE TABLE reports (
                    id INTEGER PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL,
                    details TEXT NOT NULL, longitude REAL NOT NULL, latitude REAL NOT NULL,
                    road_closed INTEGER NOT NULL, reporter TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL,
                    reviewed_at TEXT, reviewer TEXT
                )
            """)
            connection.execute("""
                CREATE TABLE report_deletions (
                    report_id INTEGER PRIMARY KEY, deleted_at TEXT NOT NULL, deleted_by TEXT NOT NULL
                )
            """)
            connection.execute("""
                INSERT INTO reports (id,kind,title,details,longitude,latitude,road_closed,reporter,status,created_at)
                VALUES (7,'idle','Keep this record','Test fixture',121.1945,24.968189,0,'preview:reporter','approved','2026-11-17'),
                       (8,'idle','Previously deleted','Test fixture',121.1945,24.968189,0,'preview:reporter','pending','2026-11-17')
            """)
            connection.execute("INSERT INTO report_deletions VALUES (8,'2026-11-17','preview:reviewer')")
        admin = self.app.test_client()
        headers = self.sign_in(admin, "reviewer")
        response = admin.get(self.prefix + "/admin/reports")
        self.assertEqual(len(response.json["reports"]), 2)
        self.assertTrue(response.json["reports"][0]["deleted_at"])
        self.assertEqual(admin.delete(self.prefix + "/admin/reports/8", json={
            "previous_status": "pending",
        }, headers=headers).status_code, 200)
        with self.app.app_context(), database() as connection:
            self.assertEqual([row["id"] for row in connection.execute("SELECT id FROM reports")], [7])
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM report_deletions").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT seq FROM sqlite_sequence WHERE name='reports'").fetchone()[0], 8)
