from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from api import api_bp
from api.construction import refresh_construction
from api.campus_account import configure_accounts
from api.campus_reports import configure_reports
from api.campus_users import configure_users

load_dotenv(Path(__file__).resolve().parent / ".env")

app = Flask(__name__)
CORS(app, origins="*") # 允許前端從發送請求

app.register_blueprint(api_bp, url_prefix="/api") # 將 API 藍圖註冊到 app 中
app.cli.add_command(refresh_construction)
configure_accounts(app)
configure_reports(app)
configure_users(app)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
