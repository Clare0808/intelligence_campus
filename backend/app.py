from flask import Flask
from flask_cors import CORS
from api import api_bp
from api.construction import refresh_construction
from api.campus_account import configure_accounts
from api.campus_reports import configure_reports

app = Flask(__name__)
CORS(app, origins="*") # 允許前端從發送請求

app.register_blueprint(api_bp, url_prefix="/api") # 將 API 藍圖註冊到 app 中
app.cli.add_command(refresh_construction)
configure_accounts(app)
configure_reports(app)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
