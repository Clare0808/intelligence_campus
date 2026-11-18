import tempfile
import json
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from api.construction_feed import ConstructionFeed, building_from_title, date_range
from api.construction_store import ConstructionStore


class ConstructionFeedTests(unittest.TestCase):
    def test_cache_migrates_once_and_hidden_setting_survives_refresh_and_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "construction.json"
            path.write_text(json.dumps({"來源": {
                "records": [{"Id": "notice"}], "status": "ready", "updated_at": "2026-11-17",
            }}), encoding="utf-8")
            feed = ConstructionFeed(path)
            self.assertEqual(feed.sources["來源"]["records"], [{"Id": "notice"}])
            self.assertTrue(feed.store.set_hidden("notice", True, False, "preview:reviewer"))
            self.assertFalse(feed.store.set_hidden("notice", False, False, "preview:reviewer"))
            with patch.dict("api.construction_feed.SOURCES", {"來源": lambda _: [{"Id": "notice", "title": "updated"}]}, clear=True):
                feed.refresh()
            restored = ConstructionFeed(path)
            self.assertEqual(restored.sources["來源"]["records"][0]["title"], "updated")
            self.assertEqual(restored.store.hidden_ids(), {"notice"})
            self.assertTrue(ConstructionStore(path.with_suffix(".sqlite3")).set_hidden(
                "notice", False, True, "preview:reviewer"
            ))
            self.assertEqual(feed.store.hidden_ids(), set())

    def test_extracts_published_date_ranges_and_keeps_unknown_end(self):
        published = date(2026, 11, 13)
        self.assertEqual(
            date_range("健雄館施工公告1151118-1120", "", published),
            ("2026-11-18", "2026-11-20"),
        )
        self.assertEqual(
            date_range("施工公告", "115年11月16日（一）起至116年6月30日（三）止", published),
            ("2026-11-16", "2027-06-30"),
        )
        self.assertEqual(
            date_range("115年8月28日起中大湖湖岸步道整修", "", published),
            ("2026-08-28", None),
        )
        self.assertEqual(date_range("115年11月30日至115年11月18日", "", published), (None, None))

    def test_only_unambiguous_building_is_matched(self):
        names = {"健雄館(科四館)": {"way/1"}, "機械館": {"way/2"}}
        self.assertEqual(building_from_title("健雄館施工公告", names), "健雄館(科四館)")
        self.assertIsNone(building_from_title("機械館旁球場施工公告", names))

    def test_failed_source_retains_its_last_successful_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "construction.json"
            feed = ConstructionFeed(path)

            def fail(_):
                raise OSError("network unavailable")

            first = {"來源甲": lambda _: [{"Id": "old"}], "來源乙": lambda _: []}
            with patch.dict("api.construction_feed.SOURCES", first, clear=True):
                self.assertEqual(feed.refresh(), 1)
                last_success = feed.snapshot()[1]["sources"][0]["updated_at"]
            second = {"來源甲": fail, "來源乙": lambda _: [{"Id": "new"}]}
            with patch.dict("api.construction_feed.SOURCES", second, clear=True):
                self.assertEqual(feed.refresh(), 2)
                records, metadata = ConstructionFeed(path).snapshot()
            self.assertEqual([record["Id"] for record in records], ["old", "new"])
            self.assertEqual(metadata["sources"][0]["status"], "error")
            self.assertEqual(metadata["sources"][0]["updated_at"], last_success)
