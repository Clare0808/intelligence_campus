from flask import Flask
from flask_cors import CORS
from api import api_bp
from api.construction import refresh_construction

app = Flask(__name__)
CORS(app, origins="*") # 允許前端從發送請求

app.register_blueprint(api_bp, url_prefix="/api") # 將 API 藍圖註冊到 app 中
app.cli.add_command(refresh_construction)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
