"""Persistent, administrator-only log of campus assistant questions."""

import os
import sqlite3
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from .campus_account import account_key, current_account
from .campus_users import admin_error


assistant_log_bp = Blueprint("campus_assistant_log", __name__, url_prefix="/api/campus")
PAGE_SIZE = 50


def configure_assistant_log(app):
    configured = os.getenv("CAMPUS_ASSISTANT_DB") or None
    app.config["CAMPUS_ASSISTANT_DB"] = str(
        Path(configured).resolve() if configured else Path(app.instance_path) / "campus-assistant.sqlite3"
    )
    app.register_blueprint(assistant_log_bp)


@contextmanager
def assistant_database():
    path = Path(current_app.config["CAMPUS_ASSISTANT_DB"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=10)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute("""CREATE TABLE IF NOT EXISTS assistant_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            account TEXT,
            created_at TEXT NOT NULL
        )""")
        yield db


def record_question(question):
    account = current_account()
    with assistant_database() as db:
        db.execute(
            "INSERT INTO assistant_questions (question, account, created_at) VALUES (?, ?, ?)",
            (question, account_key(account) if account else None, datetime.now(UTC).isoformat()),
        )


@assistant_log_bp.after_request
def disable_log_caching(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@assistant_log_bp.get("/admin/assistant/questions")
def list_questions():
    error = admin_error()
    if error:
        return error
    before = request.args.get("before")
    if before is not None and (
        not before.isascii() or not before.isdecimal() or len(before) > 18 or int(before) < 1
    ):
        return jsonify(message="紀錄頁碼無效。"), 400
    with assistant_database() as db:
        if before:
            rows = db.execute(
                "SELECT * FROM assistant_questions WHERE id < ? ORDER BY id DESC LIMIT ?",
                (int(before), PAGE_SIZE + 1),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM assistant_questions ORDER BY id DESC LIMIT ?", (PAGE_SIZE + 1,)
            ).fetchall()
    return jsonify(
        questions=[dict(row) for row in rows[:PAGE_SIZE]],
        next_before=rows[PAGE_SIZE - 1]["id"] if len(rows) > PAGE_SIZE else None,
    )