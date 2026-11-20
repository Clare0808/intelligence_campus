import json
import logging
import os
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock

import click
from flask import current_app, jsonify, request

from . import api_bp
from .crawl import run_crawler


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "school_news_processed.json"
BUILDINGS_FILE = (
    Path(__file__).resolve().parents[2]
    / "frontend" / "public" / "data" / "buildings.geojson"
)
refresh_lock = Lock()
logger = logging.getLogger(__name__)

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


def is_construction_in_next_two_weeks(construction, today):
    """只標示施工區間與今天至 14 天後（含）重疊的建築。"""
    if not isinstance(construction, dict):
        return False
    start_text = construction.get("start_date")
    end_text = construction.get("end_date")
    if not isinstance(start_text, str) or not isinstance(end_text, str):
        return False
    try:
        start = date.fromisoformat(start_text)
        end = date.fromisoformat(end_text)
    except ValueError:
        return False
    return start <= end and start <= today + timedelta(days=14) and end >= today


def current_date():
    return date.today()


def update_construction_data():
    """執行爬蟲並以原子寫入更新公告，失敗時保留舊資料。"""
    records = run_crawler()
    if not isinstance(records, list) or any(not isinstance(record, dict) for record in records):
        raise ValueError("Invalid crawler output")
    if records and not any(
        record.get("processing_status") == "success" for record in records
    ):
        raise RuntimeError("All announcements failed")

    write_json(DATA_FILE, records)
    return len(records)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    # 完整寫入暫存檔後才取代舊資料，避免 API 讀到寫入一半的 JSON。
    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(payload, temporary_file, ensure_ascii=False, indent=4)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


@click.command("refresh-construction")
def refresh_construction():
    """執行爬蟲與 AI 整理，更新後端使用的公告資料。"""
    if not refresh_lock.acquire(blocking=False):
        raise click.ClickException("公告資料正在更新中。")
    try:
        count = update_construction_data()
    except Exception as error:
        logger.exception("Construction refresh failed")
        raise click.ClickException(
            "更新失敗，原有公告資料已保留。請確認爬蟲套件、ChromeDriver 與 Azure 設定。"
        ) from error
    finally:
        refresh_lock.release()

    click.echo(f"公告資料已更新，共 {count} 筆。")


@api_bp.post("/construction/refresh")
def refresh_construction_api():
    if current_app.config["CAMPUS_ORIGIN"].startswith("https://") or os.getenv("CAMPUS_DISABLE_LEGACY_REFRESH") == "1":
        return jsonify(message="此站未開放舊版 AI 公告更新。"), 403
    if request.remote_addr not in ("127.0.0.1", "::1"):
        return jsonify(message="僅允許由本機觸發公告更新。"), 403
    if not refresh_lock.acquire(blocking=False):
        return jsonify(message="公告資料正在更新中，請稍後再試。"), 409
    feed = current_app.extensions.get("construction_feed")
    try:
        count = feed.refresh() if feed else update_construction_data()
    except Exception:
        logger.exception("Construction refresh failed")
        if feed:
            return jsonify(message="暫時無法取得校方公告，目前顯示上次成功取得的資料。"), 502
        return jsonify(message="更新失敗，原有公告資料已保留。請確認後端爬蟲設定。"), 500
    finally:
        refresh_lock.release()
    return jsonify(message=f"公告資料已更新，共 {count} 筆。", count=count)


@api_bp.get("/construction")
def get_construction(include_hidden=False):
    feed = current_app.extensions.get("construction_feed")
    live_records, metadata = feed.snapshot() if feed else ([], None)
    extra = {"refresh": metadata} if metadata else {}
    try:
        records = json.loads(DATA_FILE.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        if not live_records and not any(source["updated_at"] for source in (metadata or {}).get("sources", [])):
            return jsonify(announcements=[], building_ids=[], data_status="missing", **extra)
        records = []
    except (OSError, ValueError):
        return jsonify(message="無法讀取施工公告資料。"), 500

    if not isinstance(records, list) or any(
        not isinstance(record, dict) for record in records
    ):
        return jsonify(message="施工公告資料格式錯誤。"), 500

    if live_records:
        by_id = {record["Id"]: record for record in live_records}
        records = live_records + [record for record in records if record.get("Id") not in by_id]

    hidden = feed.store.hidden_ids() if feed else set()
    # 只處理成功抽取的施工公告，保留待確認資訊。
    announcements = [
        {
            "Id": record.get("Id"),
            "NewsTitle": record.get("NewsTitle"),
            "location": record.get("location"),
            "construction": record.get("construction"),
            "needs_review": record.get("needs_review"),
            "PublishDate": record.get("PublishDate"),
            "source_name": record.get("source_name"),
            "source_url": record.get("source_url"),
        }
        for record in records
        if record.get("processing_status") == "success"
        and record.get("announcement_type") == "construction"
        and (include_hidden or record.get("Id") not in hidden)
    ]
    if not announcements:
        return jsonify(announcements=[], building_ids=[], data_status="ready", **extra)

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

    today = current_date()
    for announcement in announcements:
        announcement["in_window"] = is_construction_in_next_two_weeks(announcement["construction"], today)
        if include_hidden:
            announcement["hidden"] = announcement["Id"] in hidden
    building_ids = sorted({
        announcement["location"]["location_id"]
        for announcement in announcements
        if announcement["location"]["location_id"] is not None
        and announcement["in_window"]
    })
    return jsonify(
        announcements=announcements, building_ids=building_ids, data_status="ready", **extra
    )
