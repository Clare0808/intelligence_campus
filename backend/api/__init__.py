from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Blueprint 建立後載入路由；匯入時不會執行爬蟲。
from . import construction
