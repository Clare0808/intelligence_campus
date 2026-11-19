import json
import os
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from openpyxl import load_workbook

from api.campus_account import configure_accounts
from api.campus_reports import configure_reports, report_store


class CampusReportsTests(unittest.TestCase):
    origin = "http://127.0.0.1:5173"
    prefix = "/api/campus"

    def setUp(self):
        folder = self.enterContext(tempfile.TemporaryDirectory())
        self.path = Path(folder) / "reports.json"
        app = Flask(__name__)
        configure_accounts(app)
        configure_reports(app)
        app.config.update(
            TESTING=True, CAMPUS_PREVIEW=True, CAMPUS_ORIGIN=self.origin,
            CAMPUS_REPORTS_FILE=str(self.path),
        )
        self.app = app

    def sign_in(self, client, role):
        response = client.get(self.prefix + "/session")
        headers = {"Origin": self.origin, "X-Campus-CSRF": response.json["csrf"]}
        response = client.post(self.prefix + "/session/preview", json={"role": role}, headers=headers)
        self.assertEqual(response.status_code, 200)
        return {**headers, "X-Campus-CSRF": response.json["csrf"]}

    def submit(self, client, headers, *, title="Test report"):
        return client.post(self.prefix + "/reports", json={
            "kind": "idle", "title": title, "details": "Test fixture",
            "longitude": 121.1945, "latitude": 24.968189,
        }, headers=headers)

    def test_review_and_export_keep_pending_private_and_cells_as_text(self):
        reporter, admin = self.app.test_client(), self.app.test_client()
        reporter_headers = self.sign_in(reporter, "reporter")
        created = self.submit(reporter, reporter_headers, title="=1+2")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json["status"], "pending")
        self.assertEqual(reporter.get(self.prefix + "/reports/map").json["reports"], [])
        self.assertEqual(reporter.get(self.prefix + "/admin/reports.xlsx").status_code, 403)
        self.assertEqual(len(json.loads(self.path.read_text(encoding="utf-8"))["reports"]), 1)

        headers = self.sign_in(admin, "reviewer")
        path = self.prefix + f"/admin/reports/{created.json['id']}"
        self.assertEqual(admin.patch(path, json={
            "status": "approved", "previous_status": "pending",
        }, headers=headers).status_code, 200)
        self.assertEqual(admin.patch(path, json={
            "status": "rejected", "previous_status": "pending",
        }, headers=headers).status_code, 409)
        published = reporter.get(self.prefix + "/reports/map").json["reports"]
        self.assertEqual(len(published), 1)
        self.assertNotIn("reporter", published[0])
        self.assertTrue(published[0]["reviewed_at"])
        response = admin.get(self.prefix + "/admin/reports")
        self.assertEqual(response.json["reports"][0]["title"], "=1+2")
        book = load_workbook(BytesIO(admin.get(self.prefix + "/admin/reports.xlsx").data))
        self.assertEqual(book.active["C2"].value, "=1+2")
        self.assertEqual(book.active["C2"].data_type, "s")

    def test_delete_is_permanent_and_ids_are_not_reused(self):
        reporter, admin = self.app.test_client(), self.app.test_client()
        reporter_headers = self.sign_in(reporter, "reporter")
        created = self.submit(reporter, reporter_headers)
        headers = self.sign_in(admin, "reviewer")
        path = self.prefix + f"/admin/reports/{created.json['id']}"
        self.assertEqual(reporter.delete(path, json={
            "previous_status": "pending",
        }, headers=reporter_headers).status_code, 403)
        self.assertEqual(admin.delete(path, json={
            "previous_status": "approved",
        }, headers=headers).status_code, 409)
        self.assertEqual(admin.delete(path, json={
            "previous_status": "pending",
        }, headers=headers).status_code, 200)
        self.assertEqual(admin.get(self.prefix + "/admin/reports").json["reports"], [])
        self.assertEqual(reporter.get(self.prefix + "/reports/map").json["reports"], [])
        self.assertEqual(load_workbook(BytesIO(
            admin.get(self.prefix + "/admin/reports.xlsx").data
        )).active.max_row, 1)
        self.assertEqual(admin.delete(path, json={
            "previous_status": "pending",
        }, headers=headers).status_code, 409)
        again = self.submit(reporter, reporter_headers)
        self.assertGreater(again.json["id"], created.json["id"])

    def test_legacy_sqlite_import_preserves_deleted_and_autoincrement_sequence(self):
        old = self.path.with_suffix(".sqlite3")
        with sqlite3.connect(old) as db:
            db.execute("""CREATE TABLE reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, title TEXT, details TEXT,
                longitude REAL, latitude REAL, road_closed INTEGER, reporter TEXT,
                status TEXT, created_at TEXT, reviewed_at TEXT, reviewer TEXT
            )""")
            db.execute("""CREATE TABLE report_deletions (
                report_id INTEGER PRIMARY KEY, deleted_at TEXT, deleted_by TEXT
            )""")
            db.execute("""INSERT INTO reports
                (id,kind,title,details,longitude,latitude,road_closed,reporter,status,created_at)
                VALUES (7,'idle','Keep this record','Test fixture',121.1945,24.968189,0,
                        'preview:reporter','approved','2026-11-17'),
                       (8,'idle','Previously deleted','Test fixture',121.1945,24.968189,0,
                        'preview:reporter','pending','2026-11-17')""")
            db.execute("INSERT INTO report_deletions VALUES (8,'2026-11-17','preview:reviewer')")
        db.close()
        self.app.config["CAMPUS_REPORTS_FILE"] = str(self.path.with_name("preview-reports.json"))
        self.path = Path(self.app.config["CAMPUS_REPORTS_FILE"])
        with patch.dict(os.environ, {"CAMPUS_REPORTS_DB": str(old)}):
            admin = self.app.test_client()
            headers = self.sign_in(admin, "reviewer")
            rows = admin.get(self.prefix + "/admin/reports").json["reports"]
            self.assertEqual([row["id"] for row in rows], [8, 7])
            self.assertTrue(rows[0]["deleted_at"])
            self.assertEqual([r["id"] for r in admin.get(
                self.prefix + "/reports/map"
            ).json["reports"]], [7])
            self.assertEqual(admin.delete(self.prefix + "/admin/reports/8", json={
                "previous_status": "pending",
            }, headers=headers).status_code, 200)
            self.assertEqual(self.path.exists(), True)
            self.assertTrue(old.exists())
            self.assertEqual(self.path.with_suffix(".sqlite3").exists(), False)
            self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["next_id"], 9)
            reporter = self.app.test_client()
            reporter_headers = self.sign_in(reporter, "reporter")
            self.assertEqual(self.submit(reporter, reporter_headers).json["id"], 9)

    def test_invalid_json_is_not_overwritten(self):
        self.path.write_text("not valid json", encoding="utf-8")
        with self.app.app_context(), self.assertRaises(json.JSONDecodeError):
            with report_store(write=True):
                pass
        self.assertEqual(self.path.read_text(encoding="utf-8"), "not valid json")

    def test_failed_atomic_replace_does_not_change_existing_report(self):
        reporter = self.app.test_client()
        headers = self.sign_in(reporter, "reporter")
        self.assertEqual(self.submit(reporter, headers).status_code, 201)
        before = self.path.read_bytes()
        with patch("api.campus_reports.os.replace", side_effect=OSError("disk unavailable")):
            with self.assertRaises(OSError):
                self.submit(reporter, headers)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_concurrent_writes_get_distinct_ids(self):
        def write_one(_):
            with self.app.app_context():
                with report_store(write=True) as data:
                    report_id = data["next_id"]
                    data["next_id"] += 1
                    return report_id

        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(write_one, range(12)))
        self.assertEqual(sorted(ids), list(range(1, 13)))
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["next_id"], 13)

    def test_legacy_database_without_autoincrement_is_imported(self):
        old = self.path.with_suffix(".sqlite3")
        db = sqlite3.connect(old)
        try:
            with db:
                db.execute("""CREATE TABLE reports (
                    id INTEGER PRIMARY KEY, kind TEXT, title TEXT, details TEXT,
                    longitude REAL, latitude REAL, road_closed INTEGER, reporter TEXT,
                    status TEXT, created_at TEXT, reviewed_at TEXT, reviewer TEXT
                )""")
                db.execute("""INSERT INTO reports VALUES
                    (3,'idle','Old report','Details',121.1945,24.968189,0,
                     'preview:reporter','pending','2026-11-17',NULL,NULL)""")
        finally:
            db.close()
        with patch.dict(os.environ, {"CAMPUS_REPORTS_DB": str(old)}):
            with self.app.app_context(), report_store() as data:
                self.assertEqual(data["reports"][0]["id"], 3)
                self.assertEqual(data["next_id"], 4)

    def test_frontend_json_is_imported_before_older_sqlite(self):
        old = self.path.parent / "frontend" / "instance" / "campus-reports.json"
        old.parent.mkdir(parents=True)
        old.write_text(json.dumps({"next_id": 4, "reports": [
            {"id": 3, "kind": "idle", "title": "Existing report", "details": "From frontend",
             "longitude": 121.1945, "latitude": 24.968189, "road_closed": False,
             "reporter": "google:reporter", "status": "pending", "created_at": "2026-11-19",
             "reviewed_at": None, "reviewer": None, "deleted_at": None, "deleted_by": None},
        ]}), encoding="utf-8")
        with sqlite3.connect(old.with_suffix(".sqlite3")) as db:
            db.execute("CREATE TABLE reports (id INTEGER PRIMARY KEY)")
        db.close()
        self.path = self.path.parent / "backend" / "instance" / "campus-reports.json"
        self.app.config["CAMPUS_REPORTS_FILE"] = str(self.path)
        with patch("api.campus_reports.legacy_json", return_value=old):
            admin = self.app.test_client()
            self.sign_in(admin, "reviewer")
            response = admin.get(self.prefix + "/admin/reports")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.json["reports"]], [3])
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["next_id"], 4)
        self.assertTrue(old.exists())

    def test_existing_backend_json_is_not_overwritten_by_frontend_json(self):
        old = self.path.parent / "frontend.json"
        old.write_text(json.dumps({"next_id": 2, "reports": []}), encoding="utf-8")
        self.path.write_text(json.dumps({"next_id": 5, "reports": []}), encoding="utf-8")
        with patch("api.campus_reports.legacy_json", return_value=old):
            with self.app.app_context(), report_store() as data:
                self.assertEqual(data["next_id"], 5)

    def test_invalid_frontend_json_is_not_replaced_or_ignored(self):
        old = self.path.parent / "frontend.json"
        old.write_text("invalid json", encoding="utf-8")
        with patch("api.campus_reports.legacy_json", return_value=old):
            with self.app.app_context(), self.assertRaises(json.JSONDecodeError):
                with report_store():
                    pass
        self.assertFalse(self.path.exists())
        self.assertEqual(old.read_text(encoding="utf-8"), "invalid json")


if __name__ == "__main__":
    unittest.main()