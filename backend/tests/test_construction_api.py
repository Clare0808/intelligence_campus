import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from app import app
from api import construction


class ConstructionApiTests(unittest.TestCase):
    def test_crawled_construction_is_returned_with_map_building_id(self):
        with tempfile.TemporaryDirectory() as directory:
            records_file = Path(directory) / "school_news_processed.json"
            buildings_file = Path(directory) / "buildings.geojson"
            records_file.write_text(json.dumps([
                {
                    "Id": "notice-1",
                    "NewsTitle": "管二施工公告",
                    "processing_status": "success",
                    "announcement_type": "construction",
                    "location": {"building": "管二", "location_id": "untrusted-id"},
                    "construction": {
                        "description": "外牆施工",
                        "start_date": date.today().isoformat(),
                        "end_date": date.today().isoformat(),
                    },
                    "needs_review": False,
                },
                {
                    "Id": "notice-2",
                    "processing_status": "failed",
                    "announcement_type": "construction",
                },
            ], ensure_ascii=False), encoding="utf-8")
            buildings_file.write_text(json.dumps({
                "type": "FeatureCollection",
                "features": [{"properties": {"id": "way/42", "name": "管理學院二館"}}],
            }, ensure_ascii=False), encoding="utf-8")

            with patch.object(construction, "DATA_FILE", records_file), patch.object(
                construction, "BUILDINGS_FILE", buildings_file
            ):
                response = app.test_client().get("/api/construction")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data_status"], "ready")
        self.assertEqual(response.json["building_ids"], ["way/42"])
        self.assertEqual(len(response.json["announcements"]), 1)
        self.assertEqual(
            response.json["announcements"][0]["location"]["location_id"], "way/42"
        )

    def test_construction_marker_only_for_dates_overlapping_next_two_weeks(self):
        today = date(2026, 11, 12)
        cases = [
            ("ongoing", "2026-11-01", "2026-11-12", True),
            ("starts_today", "2026-11-12", "2026-11-12", True),
            ("starts_on_day_14", "2026-11-26", "2026-11-27", True),
            ("finished", "2026-11-01", "2026-11-11", False),
            ("too_far", "2026-11-27", "2026-11-28", False),
            ("unknown_start", None, "2026-11-14", False),
            ("unknown_end", "2026-11-12", None, False),
            ("invalid", "not-a-date", "2026-11-14", False),
            ("reversed", "2026-11-15", "2026-11-14", False),
        ]
        for label, start, end, expected in cases:
            with self.subTest(label=label):
                with patch.object(construction, "current_date", return_value=today):
                    with tempfile.TemporaryDirectory() as directory:
                        records_file = Path(directory) / "announcements.json"
                        buildings_file = Path(directory) / "buildings.geojson"
                        records_file.write_text(json.dumps([{
                            "Id": label,
                            "processing_status": "success",
                            "announcement_type": "construction",
                            "location": {"building": "管理學院二館"},
                            "construction": {"start_date": start, "end_date": end},
                        }]), encoding="utf-8")
                        buildings_file.write_text(json.dumps({
                            "type": "FeatureCollection",
                            "features": [{"properties": {
                                "id": "way/42", "name": "管理學院二館"
                            }}],
                        }, ensure_ascii=False), encoding="utf-8")
                        with patch.object(construction, "DATA_FILE", records_file), patch.object(
                            construction, "BUILDINGS_FILE", buildings_file
                        ):
                            response = app.test_client().get("/api/construction")

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json["building_ids"], ["way/42"] if expected else [])
                self.assertEqual(len(response.json["announcements"]), 1)
                self.assertEqual(
                    response.json["announcements"][0]["location"]["location_id"],
                    "way/42",
                )

    def test_missing_crawl_output_has_explicit_status(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(construction, "DATA_FILE", Path(directory) / "missing.json"):
                response = app.test_client().get("/api/construction")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {
            "announcements": [], "building_ids": [], "data_status": "missing"
        })

    def test_refresh_endpoint_updates_saved_announcements(self):
        with tempfile.TemporaryDirectory() as directory:
            records_file = Path(directory) / "school_news_processed.json"
            records = [{"Id": "new", "processing_status": "success"}]
            with patch.object(construction, "DATA_FILE", records_file), patch.object(
                construction, "run_crawler", return_value=records
            ) as crawler:
                response = app.test_client().post("/api/construction/refresh")
            self.assertEqual(json.loads(records_file.read_text(encoding="utf-8")), records)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["count"], 1)
        crawler.assert_called_once_with()

    def test_failed_refresh_keeps_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            records_file = Path(directory) / "school_news_processed.json"
            records_file.write_text('[{"Id": "old"}]', encoding="utf-8")
            with patch.object(construction, "DATA_FILE", records_file), patch.object(
                construction, "run_crawler", side_effect=RuntimeError("private details")
            ):
                response = app.test_client().post("/api/construction/refresh")
            self.assertEqual(json.loads(records_file.read_text(encoding="utf-8")), [{"Id": "old"}])

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private details", response.json["message"])

    def test_refresh_rejects_concurrent_request(self):
        construction.refresh_lock.acquire()
        try:
            with patch.object(construction, "run_crawler") as crawler:
                response = app.test_client().post("/api/construction/refresh")
            crawler.assert_not_called()
            self.assertEqual(response.status_code, 409)
        finally:
            construction.refresh_lock.release()

    def test_refresh_rejects_non_local_request(self):
        with patch.object(construction, "run_crawler") as crawler:
            response = app.test_client().post(
                "/api/construction/refresh", environ_base={"REMOTE_ADDR": "192.0.2.5"}
            )
        self.assertEqual(response.status_code, 403)
        crawler.assert_not_called()


if __name__ == "__main__":
    unittest.main()