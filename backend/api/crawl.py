import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import json
from datetime import date
from calendar import monthrange
import os
from dotenv import load_dotenv
from openai import OpenAI

# 建立公告資訊抽取函式
def extract_announcement(announcement):

    user_prompt = f"""
        請分析以下中央大學校園公告。

        公告 ID：
        {announcement["Id"]}

        發布單位：
        {announcement["PublishDepartment"]}

        發布日期：
        {announcement["PublishDate"]}

        公告標題：
        {announcement["NewsTitle"]}

        注意：
        目前提供的資料只有公告標題與基本資訊，
        不包含公告內文。
        請勿假設你已經讀取公告內文。
    """

    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "school_construction_announcement",
                "strict": True,
                "schema": OUTPUT_SCHEMA
            }
        },
        temperature=0
    )

    result = json.loads(response.choices[0].message.content)

    return result

URL = "https://www.oga.ncu.edu.tw/f3ec03a8"

API = "https://www.oga.ncu.edu.tw/api/document/v0/list"

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Origin": "https://www.oga.ncu.edu.tw",
    "Referer": "https://www.oga.ncu.edu.tw/f3ec03a8",
    "X-Api-Key": "33341b6a.8b5e300eab8099335db12e14d795f6d4e7957e35bc8efa0bcc8e10a41d982f2e"
}

DATA = {
    "moduleUid": "ee02930e-e607-4237-8999-9e7f09c74018",
    "moduleType": "list_news",
    "enabled": True,
    "lang": "zh",
    "isFrontend": True
}

# 設定 Chrome Driver 路徑
chrome_driver_path = "C:\\Users\\User\\Documents\\chromedriver-win64\\chromedriver.exe"
service = Service(chrome_driver_path)
options = Options()

driver = webdriver.Chrome(service=service, options=options)  # 打開 Chrome 瀏覽器

driver.get(URL) # 打開目標網站

time.sleep(3)

# 取得所有 cookies
cookies = driver.get_cookies()

# 關閉瀏覽器
driver.quit()

# 轉換成 requests 可用的格式
cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies}

response = requests.post(
   API,
   headers=HEADERS, 
   json=DATA,
   cookies=cookies_dict,
   verify=False
).text

raw_data = json.loads(response)

clean_data_list = []

today = date.today()

month_offset = today.month - 6

if month_offset > 0:
    target_month = month_offset
    target_year = today.year
else:
    # 跨到上一年的處理
    target_month = month_offset + 12 # +12 換算成上一年的對應月份
    target_year = today.year - 1

# 算出 6 個月前的同一天日期
six_months_ago = date(
    target_year, 
    target_month, 
    min(today.day, monthrange(target_year, target_month)[1])
)

for data in raw_data :
    publish_date = date.fromisoformat(data["publishStartDate"])
    if not six_months_ago <= publish_date <= today:
        continue

    data_list = {}

    data_list["Id"] = data["uid"]
    data_list["PublishDepartment"] = data["teamEntity"]["name"]
    data_list["PublishDate"] = data["publishStartDate"]
    data_list["NewsTitle"] = data["name"]
    data_list["NewsContent"] = data["content"]

    clean_data_list.append(data_list)

load_dotenv()

openai_client = OpenAI(
    base_url=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)

MODEL = os.environ["AZURE_OPENAI_DEPLOYMENT"]

# 定義 JSON Schema
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "announcement_type": {
            "type": "string",
            "enum": [
                "construction",
                "road_closure",
                "maintenance",
                "facility_unavailable",
                "other",
                "not_related"
            ]
        },
        "location": {
            "type": "object",
            "properties": {
                "raw_text": {
                    "type": ["string", "null"]
                },
                "building": {
                    "type": ["string", "null"]
                },
                "relative_area": {
                    "type": ["string", "null"]
                },
                "specific_target": {
                    "type": ["string", "null"]
                },
                "location_id": {
                    "type": ["string", "null"]
                }
            },
            "required": [
                "raw_text",
                "building",
                "relative_area",
                "specific_target",
                "location_id"
            ],
            "additionalProperties": False
        },
        "construction": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": ["string", "null"]
                },
                "end_date": {
                    "type": ["string", "null"]
                },
                "description": {
                    "type": ["string", "null"]
                }
            },
            "required": [
                "start_date",
                "end_date",
                "description"
            ],
            "additionalProperties": False
        },
        "confidence": {
            "type": "number"
        },
        "needs_review": {
            "type": "boolean"
        },
        "review_reason": {
            "type": ["string", "null"]
        }
    },
    "required": [
        "announcement_type",
        "location",
        "construction",
        "confidence",
        "needs_review",
        "review_reason"
    ],
    "additionalProperties": False
}

# 設定 Agent Prompt
SYSTEM_PROMPT = """
    你是一個中央大學校園公告資訊抽取助手。

    你的任務是分析學校公告，抽取與校園施工、
    道路封閉、建築維修及設施暫停使用有關的資訊。

    【資訊抽取規則】

    1. 從公告標題辨識公告類型及施工地點。

    2. 將地點拆分為：
    - raw_text：公告中的原始地點描述
    - building：建築物名稱
    - relative_area：相對位置，例如前方、後方、周邊
    - specific_target：施工對象，例如外牆、道路、管線

    3. 將日期轉換為西元 YYYY-MM-DD 格式。
    例如：民國115年10月17日 = 2026-10-17。

    4. 區分公告發布日期與實際施工日期。
    不可以將發布日期當成施工日期。

    5. 如果只有單一施工日期，start_date 與 end_date
    可以填入相同日期。

    6. 如果公告沒有提供施工日期，填入 null。

    7. 不得自行推測公告中沒有提及的建築物、
    施工位置或日期。

    8. location_id 一律填入 null。
    此欄位將由後續校園地點比對程式處理。

    9. 如果無法確認施工地點、日期或公告類型，
    請將 needs_review 設為 true，
    並在 review_reason 說明原因。

    10. 如果公告與施工、維修、道路封閉、
        設施暫停使用無關，announcement_type
        設為 not_related。

    11. confidence 代表你對整體抽取結果的信心，
        範圍為 0 到 1。

    12. 只能根據提供的公告資訊判斷。
        不得補充外部資訊或自行猜測。

    請嚴格遵守指定的 JSON Schema。
"""

processed_data = []

for index, announcement in enumerate(clean_data_list):
    try:
        extracted_data = extract_announcement(announcement)

        # 保留原始公告資訊
        result = {
            **announcement,
            **extracted_data,
            "processing_status": "success"
        }

        processed_data.append(result)

    except Exception as e:
        processed_data.append({
            **announcement,
            "processing_status": "failed",
            "error": str(e)
        })

file_path = "school_news_processed.json"

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(
        processed_data,
        f,
        indent=4,
        ensure_ascii=False
    )
