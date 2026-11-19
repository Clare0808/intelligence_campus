from pathlib import Path

from app import app
from api.construction_feed import start_construction_feed

if __name__ == "__main__":
    app.config.update(
        CAMPUS_PREVIEW=True,
        CAMPUS_ORIGIN="http://127.0.0.1:5173",
        CAMPUS_REPORTS_FILE=str(Path(app.instance_path) / "preview-reports.json"),
        SESSION_COOKIE_NAME="ncu_campus_preview",
        SESSION_COOKIE_SECURE=False,
    )
    start_construction_feed(app)
    app.run(host="127.0.0.1", port=5000)
