import json
import math
import os
import re
import sqlite3
import tempfile
import time
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file

from .campus_account import account_key, csrf_valid, current_account

reports_bp = Blueprint("campus_reports", __name__, url_prefix="/api/campus")
KINDS = {"construction": "施工", "damage": "毀壞", "idle": "閒置"}
STATUS = {"pending": "待審核", "approved": "已公開", "rejected": "已退回"}
UNSUPPORTED_TEXT = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")
REPORT_FIELDS = (
    "id", "kind", "title", "details", "longitude", "latitude", "road_closed",
    "reporter", "status", "created_at", "reviewed_at", "reviewer", "deleted_at", "deleted_by",
)


def configure_reports(app):
    configured = os.getenv("CAMPUS_REPORTS_FILE")
    app.config["CAMPUS_REPORTS_FILE"] = str(
        Path(configured).resolve() if configured else Path(app.instance_path) / "campus-reports.json"
    )
    app.register_blueprint(reports_bp)


def legacy_json(path):
    # Older launches from frontend/ wrote to its instance directory.
    if path.parent != Path(current_app.instance_path):
        return None
    candidate = Path(current_app.root_path).parent / "frontend" / "instance" / path.name
    return candidate if candidate.is_file() else None


def legacy_databases(path):
    configured = os.getenv("CAMPUS_REPORTS_DB")
    if configured:
        return [Path(configured).resolve()]
    name = "preview-reports.sqlite3" if path.name == "preview-reports.json" else "campus-reports.sqlite3"
    backend = path.parent / name
    frontend = Path(current_app.root_path).parent / "frontend" / "instance" / name
    # When both locations exist, prefer the most recently written live database.
    if frontend.is_file() and backend.is_file():
        return [max((frontend, backend), key=lambda candidate: candidate.stat().st_mtime)]
    return [frontend, backend] if frontend.exists() else [backend, frontend]


def import_legacy(path):
    for old in legacy_databases(path):
        if not old.is_file():
            continue
        with closing(sqlite3.connect(old.as_uri() + "?mode=ro", uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            table = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='reports'"
            ).fetchone()
            if not table:
                raise ValueError(f"舊回報資料庫缺少 reports 資料表：{old}")
            deleted = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='report_deletions'"
            ).fetchone()
            joins = (
                "LEFT JOIN report_deletions ON reports.id = report_deletions.report_id"
                if deleted else ""
            )
            deletions = (
                "report_deletions.deleted_at, report_deletions.deleted_by"
                if deleted else "NULL AS deleted_at, NULL AS deleted_by"
            )
            rows = connection.execute(
                f"SELECT reports.*, {deletions} FROM reports {joins} ORDER BY reports.id DESC"
            ).fetchall()
            reports = [
                {key: (bool(row[key]) if key == "road_closed" else row[key]) for key in REPORT_FIELDS}
                for row in rows
            ]
            sequence_table = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
            ).fetchone()
            sequence = connection.execute(
                "SELECT seq FROM sqlite_sequence WHERE name='reports'"
            ).fetchone() if sequence_table else None
            next_id = max((row["id"] for row in reports), default=0) + 1
            if sequence:
                next_id = max(next_id, sequence[0] + 1)
            return {"next_id": next_id, "reports": reports}
    return {"next_id": 1, "reports": []}


def save_reports(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=path.name + ".",
            suffix=".tmp", delete=False,
        ) as output:
            temporary = Path(output.name)
            json.dump(data, output, ensure_ascii=False, indent=2, allow_nan=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_reports(path):
    if not path.exists():
        old_json = legacy_json(path)
        if old_json:
            data = read_reports(old_json)
            save_reports(path, data)
            return data
        data = import_legacy(path)
        save_reports(path, data)
        return data
    with path.open(encoding="utf-8") as source:
        data = json.load(source)
    if (
        not isinstance(data, dict) or type(data.get("next_id")) is not int
        or data["next_id"] < 1 or not isinstance(data.get("reports"), list)
        or any(not isinstance(row, dict) or not set(REPORT_FIELDS) <= row.keys()
               or type(row["id"]) is not int for row in data["reports"])
    ):
        raise ValueError("回報檔案格式無效；原檔保留，未進行寫入。")
    ids = [row["id"] for row in data["reports"]]
    if len(ids) != len(set(ids)) or any(
        row_id < 1 or row_id >= data["next_id"] for row_id in ids
    ):
        raise ValueError("回報檔案編號無效；原檔保留，未進行寫入。")
    return data


@contextmanager
def report_store(*, write=False):
    path = Path(current_app.config["CAMPUS_REPORTS_FILE"])
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep a separate lock file: replacing the JSON must not change the lock inode.
    with (path.parent / (path.name + ".lock")).open("a+b") as lock:
        if os.name == "nt":
            import msvcrt

            for attempt in range(100):
                try:
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if attempt == 99:
                        raise TimeoutError("回報檔案正忙碌，請稍後重試。")
                    time.sleep(0.1)
        else:
            import fcntl

            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            data = read_reports(path)
            yield data
            if write:
                save_reports(path, data)
        finally:
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def now():
    return datetime.now(UTC).isoformat(timespec="seconds")


def json_body():
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else {}


def valid_coordinate(value, lower, upper):
    return type(value) in (int, float) and lower <= value <= upper and math.isfinite(value)


def valid_text(value, limit):
    return (
        isinstance(value, str)
        and 1 <= len(value.strip()) <= limit
        and UNSUPPORTED_TEXT.search(value) is None
    )


def report_rows(data):
    return sorted(data["reports"], key=lambda row: row["id"], reverse=True)


def authorization_error(account, *, admin=False, write=False):
    if not account:
        return jsonify(message="請先登入。"), 401
    if admin and not account["admin"]:
        return jsonify(message="需要管理員權限。"), 403
    if write and not csrf_valid():
        return jsonify(message="工作階段已更新，請重新整理頁面。"), 403
    return None


@reports_bp.after_request
def disable_report_caching(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@reports_bp.get("/reports/map")
def published_reports():
    with report_store() as data:
        fields = ("id", "kind", "title", "details", "longitude", "latitude",
                  "road_closed", "created_at", "reviewed_at")
        return jsonify(reports=[
            {key: row[key] for key in fields}
            for row in report_rows(data)
            if row["status"] == "approved" and not row["deleted_at"]
        ])


@reports_bp.post("/reports")
def submit_report():
    account = current_account()
    error = authorization_error(account, write=True)
    if error:
        return error
    request.max_content_length = 12 * 1024
    data = json_body()
    kind = data.get("kind")
    title = data.get("title")
    details = data.get("details")
    longitude = data.get("longitude")
    latitude = data.get("latitude")
    road_closed = data.get("road_closed", False)
    if (
        not isinstance(kind, str) or kind not in KINDS
        or not valid_text(title, 80)
        or not valid_text(details, 1000)
        or not valid_coordinate(longitude, 121.1843596, 121.1980519)
        or not valid_coordinate(latitude, 24.9635065, 24.9722322)
        or type(road_closed) is not bool
        or (road_closed and kind != "construction")
    ):
        return jsonify(message="請填寫有效的類別、標題、說明及校園位置。"), 400
    with report_store(write=True) as store:
        report_id = store["next_id"]
        store["next_id"] += 1
        store["reports"].append({
            "id": report_id, "kind": kind, "title": title.strip(),
            "details": details.strip(), "longitude": longitude, "latitude": latitude,
            "road_closed": road_closed, "reporter": account_key(account),
            "status": "pending", "created_at": now(), "reviewed_at": None,
            "reviewer": None, "deleted_at": None, "deleted_by": None,
        })
    return jsonify(id=report_id, status="pending"), 201


@reports_bp.get("/admin/reports")
def admin_reports():
    error = authorization_error(current_account(), admin=True)
    if error:
        return error
    with report_store() as data:
        return jsonify(reports=report_rows(data))


@reports_bp.patch("/admin/reports/<int:report_id>")
def review_report(report_id):
    account = current_account()
    error = authorization_error(account, admin=True, write=True)
    if error:
        return error
    data = json_body()
    status = data.get("status")
    previous_status = data.get("previous_status")
    if (
        status not in ("approved", "rejected")
        or previous_status not in tuple(STATUS)
        or status == previous_status
    ):
        return jsonify(message="審核狀態無效。"), 400
    with report_store(write=True) as store:
        row = next((row for row in store["reports"] if row["id"] == report_id), None)
        if not row or row["status"] != previous_status or row["deleted_at"]:
            return jsonify(message="此筆回報已變更或不存在，請重新載入。"), 409
        row.update(status=status, reviewed_at=now(), reviewer=account_key(account))
    return jsonify(status=status)


@reports_bp.delete("/admin/reports/<int:report_id>")
def delete_report(report_id):
    account = current_account()
    error = authorization_error(account, admin=True, write=True)
    if error:
        return error
    previous = json_body().get("previous_status")
    if previous not in tuple(STATUS):
        return jsonify(message="回報狀態無效。"), 400
    with report_store(write=True) as store:
        row = next((row for row in store["reports"] if row["id"] == report_id), None)
        if not row or row["status"] != previous:
            return jsonify(message="此筆回報已變更或不存在，請重新載入。"), 409
        store["reports"].remove(row)
    return jsonify(message="回報已從檔案永久刪除。")


@reports_bp.get("/admin/construction")
def admin_construction():
    error = authorization_error(current_account(), admin=True)
    if error:
        return error
    from .construction import get_construction

    return get_construction(include_hidden=True)


@reports_bp.post("/admin/construction/visibility")
def change_construction_visibility():
    account = current_account()
    error = authorization_error(account, admin=True, write=True)
    if error:
        return error
    feed = current_app.extensions.get("construction_feed")
    if not feed:
        return jsonify(message="此啟動模式尚未啟用校方公告管理，請使用本機預覽。"), 503
    data = json_body()
    notice_id = data.get("id")
    hidden = data.get("hidden")
    previous = data.get("previous_hidden")
    if not isinstance(notice_id, str) or type(hidden) is not bool or type(previous) is not bool:
        return jsonify(message="公告設定無效。"), 400
    from .construction import get_construction

    response = get_construction(include_hidden=True)
    if isinstance(response, tuple):
        return response
    if not any(notice["Id"] == notice_id for notice in response.json["announcements"]):
        return jsonify(message="找不到此筆公告，請重新載入。"), 404
    if not feed.store.set_hidden(notice_id, hidden, previous, account_key(account)):
        return jsonify(message="公告已由其他操作變更，請重新載入。"), 409
    return jsonify(message="公告已隱藏。" if hidden else "公告已還原。")


@reports_bp.get("/admin/reports.xlsx")
def export_reports():
    error = authorization_error(current_account(), admin=True)
    if error:
        return error
    from openpyxl import Workbook

    book = Workbook()
    sheet = book.active
    sheet.title = "校園回報"
    sheet.append(["編號", "類別", "標題", "說明", "經度", "緯度", "道路封閉", "審核狀態",
                  "回報帳號", "回報時間 (UTC)", "審核帳號", "審核時間 (UTC)"])
    with report_store() as data:
        for row in report_rows(data):
            if row["deleted_at"]:
                continue
            sheet.append([
                row["id"], KINDS[row["kind"]], row["title"], row["details"],
                row["longitude"], row["latitude"], "是" if row["road_closed"] else "否",
                STATUS[row["status"]], row["reporter"], row["created_at"],
                row["reviewer"], row["reviewed_at"],
            ])
            # User-supplied values must remain text even when they start with '='.
            for column in (3, 4):
                sheet.cell(sheet.max_row, column).data_type = "s"
    sheet.freeze_panes = "C2"
    sheet.auto_filter.ref = sheet.dimensions
    for column, width in zip("ABCDEFGHIJKL", (7, 12, 30, 55, 14, 14, 12, 12, 26, 27, 26, 27)):
        sheet.column_dimensions[column].width = width
    output = BytesIO()
    book.save(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="campus-reports.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")