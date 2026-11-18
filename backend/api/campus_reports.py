import math
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file

from .campus_account import account_key, csrf_valid, current_account

reports_bp = Blueprint("campus_reports", __name__, url_prefix="/api/campus")
KINDS = {"construction": "施工", "damage": "毀壞", "idle": "閒置"}
STATUS = {"pending": "待審核", "approved": "已公開", "rejected": "已退回"}
UNSUPPORTED_TEXT = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")
REPORT_SCHEMA = """
    CREATE TABLE reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,
        title TEXT NOT NULL,
        details TEXT NOT NULL,
        longitude REAL NOT NULL,
        latitude REAL NOT NULL,
        road_closed INTEGER NOT NULL,
        reporter TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL,
        reviewed_at TEXT,
        reviewer TEXT
    )
"""


def configure_reports(app):
    app.config["CAMPUS_REPORTS_DB"] = os.getenv(
        "CAMPUS_REPORTS_DB", str(Path(app.instance_path) / "campus-reports.sqlite3")
    )
    app.register_blueprint(reports_bp)


@contextmanager
def database():
    path = Path(current_app.config["CAMPUS_REPORTS_DB"])
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute(REPORT_SCHEMA.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1))
            schema = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'reports'"
            ).fetchone()[0]
            if "AUTOINCREMENT" not in schema.upper():
                # Retried deletes must never target a later report reusing an old ID.
                connection.execute("BEGIN IMMEDIATE")
                schema = connection.execute(
                    "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'reports'"
                ).fetchone()[0]
                if "AUTOINCREMENT" not in schema.upper():
                    connection.execute("ALTER TABLE reports RENAME TO reports_before_id_migration")
                    connection.execute(REPORT_SCHEMA)
                    connection.execute("""
                        INSERT INTO reports
                            (id, kind, title, details, longitude, latitude, road_closed,
                             reporter, status, created_at, reviewed_at, reviewer)
                        SELECT id, kind, title, details, longitude, latitude, road_closed,
                               reporter, status, created_at, reviewed_at, reviewer
                        FROM reports_before_id_migration
                    """)
                    connection.execute("DROP TABLE reports_before_id_migration")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS report_deletions (
                    report_id INTEGER PRIMARY KEY,
                    deleted_at TEXT NOT NULL,
                    deleted_by TEXT NOT NULL
                )
            """)
            yield connection
    finally:
        connection.close()


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


def report_rows(connection):
    return connection.execute("""
        SELECT reports.*, deleted_at, deleted_by
        FROM reports LEFT JOIN report_deletions ON reports.id = report_id
        ORDER BY reports.id DESC
    """)


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
    with database() as connection:
        rows = connection.execute("""
            SELECT id, kind, title, details, longitude, latitude, road_closed,
                   created_at, reviewed_at
            FROM reports WHERE status = 'approved'
            AND NOT EXISTS (SELECT 1 FROM report_deletions WHERE report_id = reports.id)
            ORDER BY id DESC
        """)
        return jsonify(reports=[dict(row) for row in rows])


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
    with database() as connection:
        result = connection.execute("""
            INSERT INTO reports (kind, title, details, longitude, latitude,
                                 road_closed, reporter, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            kind, title.strip(), details.strip(), longitude, latitude,
            road_closed, account_key(account), now(),
        ))
        report_id = result.lastrowid
    return jsonify(id=report_id, status="pending"), 201


@reports_bp.get("/admin/reports")
def admin_reports():
    error = authorization_error(current_account(), admin=True)
    if error:
        return error
    with database() as connection:
        return jsonify(reports=[dict(row) for row in report_rows(connection)])


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
    with database() as connection:
        update = connection.execute("""
            UPDATE reports SET status = ?, reviewed_at = ?, reviewer = ?
            WHERE id = ? AND status = ?
            AND NOT EXISTS (SELECT 1 FROM report_deletions WHERE report_id = reports.id)
        """, (status, now(), account_key(account), report_id, previous_status))
        if not update.rowcount:
            return jsonify(message="此筆回報已變更或不存在，請重新載入。"), 409
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
    with database() as connection:
        result = connection.execute("""
            DELETE FROM reports WHERE id = ? AND status = ?
        """, (report_id, previous))
        if not result.rowcount:
            return jsonify(message="此筆回報已變更或不存在，請重新載入。"), 409
        connection.execute("DELETE FROM report_deletions WHERE report_id = ?", (report_id,))
    return jsonify(message="回報已從資料庫永久刪除。")


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
    with database() as connection:
        for row in report_rows(connection):
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
