import os
import sqlite3
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

users_bp = Blueprint("campus_users", __name__, url_prefix="/api/campus")
OWNER_EMAIL = "yuhsin099@gmail.com"


def configure_users(app):
    configured = os.getenv("CAMPUS_USERS_DB") or None
    app.config["CAMPUS_USERS_DB"] = str(
        Path(configured).resolve() if configured else Path(app.instance_path) / "campus-users.sqlite3"
    )
    app.register_blueprint(users_bp)


@contextmanager
def user_database():
    path = Path(current_app.config["CAMPUS_USERS_DB"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=10)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            provider TEXT NOT NULL,
            subject TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            email_verified INTEGER NOT NULL,
            role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
            last_login_at TEXT NOT NULL,
            PRIMARY KEY (provider, subject)
        )""")
        yield db


def is_owner(provider, email, verified):
    return (
        provider == "google" and verified is True
        and isinstance(email, str) and email.lower() == OWNER_EMAIL
    )


def record_login(provider, subject, name, email, verified):
    with user_database() as db:
        if is_owner(provider, email, verified):
            db.execute("BEGIN IMMEDIATE")
            owner = db.execute("SELECT subject FROM users WHERE provider='google' AND lower(email)=? AND email_verified=1",
                               (OWNER_EMAIL,)).fetchone()
            if owner and owner["subject"] != subject:
                raise ValueError("初始管理員電子郵件與現有帳號識別不符。")
        db.execute("""INSERT INTO users
            (provider, subject, name, email, email_verified, last_login_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider, subject) DO UPDATE SET
                name=excluded.name, email=excluded.email,
                email_verified=excluded.email_verified, last_login_at=excluded.last_login_at
        """, (provider, subject, name, email, int(verified), datetime.now(UTC).isoformat()))


def user_role(provider, subject):
    with user_database() as db:
        row = db.execute("SELECT * FROM users WHERE provider=? AND subject=?", (provider, subject)).fetchone()
    return public_user(row)["role"] if row else "user"


def public_user(row):
    verified = bool(row["email_verified"])
    owner = is_owner(row["provider"], row["email"], verified)
    return {
        "provider": row["provider"], "subject": row["subject"],
        "name": row["name"], "email": row["email"],
        "email_verified": verified, "role": "admin" if owner else row["role"],
        "owner": owner, "last_login_at": row["last_login_at"],
    }


def admin_error(*, write=False):
    from .campus_account import csrf_valid, current_account

    account = current_account()
    if not account:
        return jsonify(message="請先登入。"), 401
    if not account["admin"]:
        return jsonify(message="需要管理員權限。"), 403
    if write and not csrf_valid():
        return jsonify(message="工作階段已更新，請重新整理頁面。"), 403
    return None


@users_bp.get("/admin/users")
def list_users():
    error = admin_error()
    if error:
        return error
    with user_database() as db:
        rows = db.execute("SELECT * FROM users ORDER BY last_login_at DESC").fetchall()
    return jsonify(users=[public_user(row) for row in rows])


@users_bp.patch("/admin/users/<provider>/<subject>")
def change_user_role(provider, subject):
    error = admin_error(write=True)
    if error:
        return error
    data = request.get_json(silent=True)
    role = data.get("role") if isinstance(data, dict) else None
    previous = data.get("previous_role") if isinstance(data, dict) else None
    if role not in ("user", "admin") or previous not in ("user", "admin"):
        return jsonify(message="使用者權限無效。"), 400
    with user_database() as db:
        db.execute("BEGIN IMMEDIATE")
        from .campus_account import current_account

        if not current_account()["admin"]:
            return jsonify(message="需要管理員權限。"), 403
        row = db.execute("SELECT * FROM users WHERE provider=? AND subject=?", (provider, subject)).fetchone()
        if not row:
            return jsonify(message="找不到此使用者，請重新載入。"), 404
        user = public_user(row)
        if user["owner"]:
            return jsonify(message="初始管理員權限不可修改。"), 403
        if user["role"] != previous:
            return jsonify(message="此使用者權限已變更，請重新載入。"), 409
        db.execute("UPDATE users SET role=? WHERE provider=? AND subject=?", (role, provider, subject))
    return jsonify(role=role)