import os
import secrets
from datetime import timedelta
from urllib.parse import urlsplit

from flask import Blueprint, current_app, jsonify, redirect, request, session
from .campus_users import record_login, user_role

account_bp = Blueprint("campus_account", __name__, url_prefix="/api/campus")
PROVIDERS = {
    "google": (
        "Google",
        "https://accounts.google.com/.well-known/openid-configuration",
        "openid profile email",
    ),
}


def configure_accounts(app):
    secret = os.getenv("CAMPUS_SESSION_SECRET", "")
    origin = os.getenv("CAMPUS_ORIGIN", "http://127.0.0.1:5173").rstrip("/")
    app.config.update(
        SECRET_KEY=secret or secrets.token_hex(32),
        SESSION_COOKIE_NAME="ncu_campus",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=origin.startswith("https://"),
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        CAMPUS_ORIGIN=origin,
        CAMPUS_PREVIEW=False,
    )
    active = {}
    for provider, (_, metadata, scope) in PROVIDERS.items():
        client_id = os.getenv(f"CAMPUS_{provider.upper()}_CLIENT_ID")
        client_secret = os.getenv(f"CAMPUS_{provider.upper()}_CLIENT_SECRET")
        if secret and client_id and client_secret:
            active[provider] = {
                "client_id": client_id,
                "client_secret": client_secret,
                "server_metadata_url": metadata,
                "client_kwargs": {"scope": scope, "code_challenge_method": "S256"},
            }
    if active:
        from authlib.integrations.flask_client import OAuth

        oauth = OAuth(app)
        for provider, options in active.items():
            oauth.register(provider, **options)
        app.extensions["campus_oauth"] = oauth
    app.config["CAMPUS_PROVIDERS"] = tuple(active)
    app.register_blueprint(account_bp)


def preview_available():
    return (
        current_app.config["CAMPUS_PREVIEW"]
        and request.remote_addr in ("127.0.0.1", "::1")
        and urlsplit(f"//{request.host}").hostname in ("127.0.0.1", "localhost", "::1")
    )


def current_account():
    account = session.get("campus_account")
    if not account:
        return None
    if account["provider"] == "preview":
        if not preview_available():
            return None
        admin = account["subject"] == "reviewer"
    else:
        admin = user_role(account["provider"], account["subject"]) == "admin"
    return {**account, "admin": admin}


def account_key(account):
    return f"{account['provider']}:{account['subject']}"


def csrf_valid():
    token = session.get("campus_csrf")
    provided = request.headers.get("X-Campus-CSRF", "")
    return bool(
        token
        and provided.isascii()
        and secrets.compare_digest(token, provided)
        and request.headers.get("Origin") == current_app.config["CAMPUS_ORIGIN"]
    )


def session_data():
    return {
        "account": current_account(),
        "providers": [
            {"id": provider, "label": label, "enabled": provider in current_app.config["CAMPUS_PROVIDERS"]}
            for provider, (label, _, _) in PROVIDERS.items()
        ],
        "preview": preview_available(),
        "csrf": session.setdefault("campus_csrf", secrets.token_urlsafe(32)),
    }


def sign_in(provider, subject, name, *, email=None, email_verified=False):
    session.clear()
    session.permanent = True
    session["campus_account"] = {
        "provider": provider, "subject": subject, "name": name,
        "email": email, "email_verified": email_verified,
    }


@account_bp.after_request
def disable_account_caching(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@account_bp.get("/session")
def get_session():
    return jsonify(session_data())


@account_bp.post("/session/preview")
def preview_login():
    if not preview_available() or not csrf_valid():
        return jsonify(message="本機預覽登入無法使用。"), 403
    data = request.get_json(silent=True)
    role = data.get("role") if isinstance(data, dict) else None
    if role not in ("reporter", "reviewer"):
        return jsonify(message="請選擇預覽角色。"), 400
    sign_in("preview", role, "預覽管理員" if role == "reviewer" else "預覽回報者")
    return jsonify(session_data())


@account_bp.post("/session/logout")
def logout():
    if not csrf_valid():
        return jsonify(message="工作階段已更新，請重新整理頁面。"), 403
    session.clear()
    return jsonify(session_data())


@account_bp.get("/login/<provider>")
def login(provider):
    origin = current_app.config["CAMPUS_ORIGIN"]
    if provider not in current_app.config["CAMPUS_PROVIDERS"]:
        return redirect(f"{origin}/campus?login=unavailable")
    client = current_app.extensions["campus_oauth"].create_client(provider)
    callback = f"{origin}/api/campus/callback/{provider}"
    try:
        return client.authorize_redirect(callback)
    except Exception:
        current_app.logger.warning("Campus login initiation failed for %s", provider)
        return redirect(f"{origin}/campus?login=failed")


@account_bp.get("/callback/<provider>")
def callback(provider):
    origin = current_app.config["CAMPUS_ORIGIN"]
    if provider not in current_app.config["CAMPUS_PROVIDERS"]:
        return redirect(f"{origin}/campus?login=unavailable")
    client = current_app.extensions["campus_oauth"].create_client(provider)
    try:
        claims = client.authorize_access_token().get("userinfo", {})
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            return redirect(f"{origin}/campus?login=failed")
        name = claims.get("name")
        email = claims.get("email")
        name = name[:120] if isinstance(name, str) and name else PROVIDERS[provider][0]
        email = email if isinstance(email, str) else None
        verified = claims.get("email_verified") is True
        record_login(provider, subject, name, email, verified)
        sign_in(
            provider, subject, name, email=email, email_verified=verified,
        )
    except Exception:
        current_app.logger.warning("Campus login callback failed for %s", provider)
        return redirect(f"{origin}/campus?login=failed")
    return redirect(f"{origin}/campus?login=success")
