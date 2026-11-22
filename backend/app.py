import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, send_from_directory
from api import api_bp
from api.construction import refresh_construction
from api.campus_account import configure_accounts
from api.campus_reports import configure_reports
from api.campus_users import configure_users
from api.campus_assistant import assistant_bp
from api.campus_assistant_log import configure_assistant_log

load_dotenv(Path(__file__).resolve().parent / ".env")

app = Flask(__name__)

if os.getenv("CAMPUS_DATA_DIR"):
    app.instance_path = str(Path(os.environ["CAMPUS_DATA_DIR"]).resolve())
if os.getenv("CAMPUS_ORIGIN", "http://127.0.0.1:5173").startswith("https://") and not os.getenv("CAMPUS_SESSION_SECRET"):
    raise RuntimeError("CAMPUS_SESSION_SECRET is required for HTTPS deployment")

app.register_blueprint(api_bp, url_prefix="/api")
app.register_blueprint(assistant_bp)
app.cli.add_command(refresh_construction)
configure_accounts(app)
configure_reports(app)
configure_users(app)
configure_assistant_log(app)

# The built Vue application and API share one origin in production. Vite still
# serves the frontend and proxies /api during local development.
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
@app.get("/<path:filename>")
def frontend(filename=""):
    if filename.startswith("api/") or filename == "api":
        abort(404)
    if filename and (frontend_dist / filename).is_file():
        return send_from_directory(frontend_dist, filename)
    if filename and "." in filename.rsplit("/", 1)[-1]:
        abort(404)
    return send_from_directory(frontend_dist, "index.html")


if os.getenv("CAMPUS_START_CONSTRUCTION_FEED") == "1":
    from api.construction_feed import start_construction_feed

    start_construction_feed(app)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
