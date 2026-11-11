import json
import unicodedata
from pathlib import Path
from tempfile import NamedTemporaryFile

import click
from flask import jsonify

from . import api_bp
from .crawl import run_crawler


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "school_news_processed.json"
BUILDINGS_FILE = (
    Path(__file__).resolve().parents[2]
    / "frontend" / "public" / "data" / "buildings.geojson"
)

# 別名明確對應到目前 GeoJSON 的名稱，不使用模糊搜尋猜測建築。
BUILDING_ALIASES = {
    "管二": "管理學院二館",
    "管理二館": "管理學院二館",
}


def normalize_name(name):
    if not isinstance(name, str):
        return ""
    return "".join(unicodedata.normalize("NFKC", name).split()).casefold()


def build_name_index(features):
    index = {}
    for feature_index, feature in enumerate(features):
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            continue
        name = normalize_name(properties.get("name"))
        building_id = properties.get("id")
        if building_id is None:
            # 與前端 prepareBuildings 的 nullish fallback 一致，使用原始陣列索引。
            building_id = f"local/building-{feature_index}"
        if name and isinstance(building_id, str) and building_id:
            index.setdefault(name, set()).add(building_id)
    return index


def match_building(name, name_index):
    name = normalize_name(name)
    name = normalize_name(BUILDING_ALIASES.get(name, name))
    matches = name_index.get(name, set())
    return next(iter(matches)) if len(matches) == 1 else None


@click.command("refresh-construction")
def refresh_construction():
    """執行爬蟲與 AI 整理，更新後端使用的公告資料。"""
    try:
        records = run_crawler()
        if records and not any(
            record.get("processing_status") == "success" for record in records
        ):
            raise RuntimeError("All announcements failed")

        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        # 完整寫入暫存檔後才取代舊資料，避免 API 讀到寫入一半的 JSON。
        temporary_path = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=DATA_FILE.parent, delete=False
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(records, temporary_file, ensure_ascii=False, indent=4)
            temporary_path.replace(DATA_FILE)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
    except Exception:
        raise click.ClickException(
            "更新失敗，原有公告資料已保留。請確認爬蟲套件、ChromeDriver 與 Azure 設定。"
        ) from None

    click.echo(f"公告資料已更新，共 {len(records)} 筆。")


@api_bp.get("/construction")
def get_construction():
    try:
        records = json.loads(DATA_FILE.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return jsonify(announcements=[], building_ids=[], data_status="missing")
    except (OSError, ValueError):
        return jsonify(message="無法讀取施工公告資料。"), 500

    if not isinstance(records, list) or any(
        not isinstance(record, dict) for record in records
    ):
        return jsonify(message="施工公告資料格式錯誤。"), 500

    # 只處理成功抽取的施工公告，保留待確認資訊。
    announcements = [
        {
            "Id": record.get("Id"),
            "NewsTitle": record.get("NewsTitle"),
            "location": record.get("location"),
            "construction": record.get("construction"),
            "needs_review": record.get("needs_review"),
        }
        for record in records
        if record.get("processing_status") == "success"
        and record.get("announcement_type") == "construction"
    ]
    if not announcements:
        return jsonify(announcements=[], building_ids=[], data_status="ready")

    try:
        buildings = json.loads(BUILDINGS_FILE.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return jsonify(message="無法讀取地圖建築資料。"), 500
    if (
        not isinstance(buildings, dict)
        or buildings.get("type") != "FeatureCollection"
        or not isinstance(buildings.get("features"), list)
    ):
        return jsonify(message="地圖建築資料格式錯誤。"), 500

    name_index = build_name_index(buildings["features"])
    for announcement in announcements:
        location = announcement["location"]
        if not isinstance(location, dict):
            location = {}
        # 由後端重新確認 ID，避免直接採信 AI 產生的 ID。
        announcement["location"] = {
            **location,
            "location_id": match_building(location.get("building"), name_index),
        }

    building_ids = sorted({
        announcement["location"]["location_id"]
        for announcement in announcements
        if announcement["location"]["location_id"] is not None
    })
    return jsonify(
        announcements=announcements, building_ids=building_ids, data_status="ready"
    )
