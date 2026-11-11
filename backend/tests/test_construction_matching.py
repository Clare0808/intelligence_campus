import json
import unittest
from collections import Counter

from api.construction import (
    BUILDINGS_FILE,
    build_name_index,
    match_building,
    normalize_name,
)


class ConstructionMatchingTests(unittest.TestCase):
    def test_missing_and_null_ids_use_original_feature_index(self):
        features = [
            {"properties": {"id": "way/known", "name": "總圖書館"}},
            {"properties": {"name": None}},
            {"properties": {"name": "機械館"}},
            {"properties": {"id": None, "name": "室內游泳池"}},
        ]
        index = build_name_index(features)
        self.assertEqual(match_building("總圖書館", index), "way/known")
        self.assertEqual(match_building("機械館", index), "local/building-2")
        self.assertEqual(match_building("室內游泳池", index), "local/building-3")
        self.assertNotIn("id", features[2]["properties"])

    def test_explicit_id_is_preserved_and_alias_still_works(self):
        index = build_name_index([
            {"properties": {"id": "way/known", "name": "管理學院二館"}},
        ])
        self.assertEqual(match_building("管二", index), "way/known")

    def test_ambiguous_names_remain_unmatched_with_fallback_ids(self):
        index = build_name_index([
            {"properties": {"name": "同名建築"}},
            {"properties": {"name": "同名建築"}},
        ])
        self.assertIsNone(match_building("同名建築", index))
        self.assertIsNone(match_building("未知建築", index))

    def test_current_map_fallback_ids_match_frontend_rule(self):
        features = json.loads(BUILDINGS_FILE.read_text(encoding="utf-8-sig"))["features"]
        index = build_name_index(features)
        counts = Counter(normalize_name(f["properties"].get("name")) for f in features)
        for feature_index, feature in enumerate(features):
            properties = feature["properties"]
            name = properties.get("name")
            if properties.get("id") is None and name and counts[normalize_name(name)] == 1:
                with self.subTest(name=name):
                    self.assertEqual(
                        match_building(name, index), f"local/building-{feature_index}"
                    )


if __name__ == "__main__":
    unittest.main()
