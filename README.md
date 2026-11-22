# 中央大學 3D 校園地圖

首頁 `/` 使用 Vue 3、MapLibre GL JS、GeoJSON 與 OpenFreeMap 底圖顯示中央大學周邊的 OSM 建築輪廓、道路及 `fill-extrusion` 量體。原本未經測繪的 SVG 示意圖和其路線功能保留於 `/map`，**不可用於導航**。

## 啟動與檢查

```sh
npm install
npm run dev
npm run lint
npm run build
```

上述指令請在 `frontend/` 目錄執行。若要顯示施工公告，需另外啟動 Flask 後端：

```sh
cd backend
python app.py
```

在另一個終端機啟動前端（於 `frontend/` 執行 `npm run dev`），Vite 會將 `/api` 代理至 `http://127.0.0.1:5000`。首頁 `/` 的 3D 地圖會向 `/api/construction` 讀取公告；只有能明確對應建築、且施工期間與今天至 14 天後（含）重疊的公告才會標紅建築。已完工、距今超過兩週才開始，或缺少有效起訖日期的公告不會標紅，但仍可在點選建築後查看。若沒有整理後的資料，畫面會顯示「尚無施工公告資料」。側邊欄的「更新施工公告」按鈕會呼叫 `POST /api/construction/refresh` 執行爬蟲與 AI 整理；等待期間全頁顯示載入動畫，成功後顯示「資料更新成功!正在重新整理...」並自動重新整理頁面。更新失敗時會關閉遮罩、顯示錯誤且不重新整理；開啟頁面本身不會自動爬取。

需要更新公告時，請先在後端環境安裝 Flask、flask-cors、click、python-dotenv、openai、requests、selenium，並設定 `backend/.env` 所需的 `AZURE_OPENAI_ENDPOINT`、`AZURE_OPENAI_API_KEY`、`AZURE_OPENAI_DEPLOYMENT`；爬蟲目前也使用 `backend/api/crawl.py` 中指定的 ChromeDriver 路徑，執行前須確認符合本機環境（直接在 `backend/` 執行以下指令可載入該目錄的 `.env`）：

```sh
python -m flask --app app refresh-construction
```

此指令與側邊欄按鈕都會在成功後更新 `backend/data/school_news_processed.json`，供 API 讀取。請勿將 `.env` 或含敏感資訊的爬取結果提交到版本控制。**更新端點目前只接受後端所見的本機位址（開發時透過 Vite 本機代理），沒有登入驗證；僅適用於可信任的本機開發環境。若公開部署或讓其他使用者透過代理存取，務必先加上身分驗證及請求頻率限制，避免消耗爬蟲與 AI 額度。**後端測試可於 `backend/` 執行 `python -m unittest discover -s tests -v`。

地圖底圖需網路連線；建築及道路 GeoJSON 已存放在 `public/data/`，無須瀏覽器對 Overpass 發送請求。拖曳平移、右鍵拖曳旋轉／傾斜、滾輪縮放，亦可使用右上角控制鈕。點建物或搜尋名稱可顯示資訊並高亮。位置與道路來自 OSM WGS84 資料，與底圖使用相同座標系統；OSM 資料不代表官方測繪成果。

## 資料與限制

校園地圖 `/campus` 右下角提供 AI 助手聊天室，可輸入問題或點選快速提問。後端 `POST /api/campus/assistant/chat` 沿用公告抽取程式的 OpenAI 相容模型設定；請設定 `backend/.env` 的 `AZURE_OPENAI_ENDPOINT`（HTTPS 的 OpenAI 相容 base URL）、`AZURE_OPENAI_API_KEY` 和 `AZURE_OPENAI_DEPLOYMENT`。前端不會取得金鑰；回答取得後在聊天室逐字顯示（非模型即時串流）。助手僅參考近期已整理且無待確認標記的施工公告與部分已審核回報；封路回報沒有有效期限，請勿據此認定目前道路仍封閉。資訊僅供參考，實際通行以現場與校方公告為準。

已通過驗證的 AI 提問會記錄在 `backend/instance/campus-assistant.sqlite3` 的 `assistant_questions` 資料表（可用 `CAMPUS_ASSISTANT_DB` 指定其他路徑），包含問題、UTC 時間及登入帳號識別；未登入則標記為訪客。不保存模型回答或對話歷史；即使模型回覆失敗仍會保留提問。管理員可在後台「AI 提問紀錄」查看，每次載入 50 筆；一般使用者無法讀取。請保護並定期備份資料庫；不應將其提交到版本控制。若部署環境未提供持久化儲存，重新部署後紀錄可能遺失。

- OSM 資料：[OpenStreetMap API bounding box 匯出](https://api.openstreetmap.org/api/0.6/map?bbox=121.18485,24.96505,121.19675,24.9717)，校園參考為 [OSM relation 18727079](https://www.openstreetmap.org/relation/18727079)。擷取日期 2026-11-09。轉成 128 個建築輪廓（71 個具名稱）、164 條道路／步道；資料授權 [ODbL](https://www.openstreetmap.org/copyright)，© OpenStreetMap contributors。此 bbox 涵蓋校園及鄰近區域，**不是正式校園邊界裁切**，因此部分輪廓及道路位於校外。
- [中央大學官方校園導覽圖片](https://www.ncu.edu.tw/var/file/0/1000/img/3/712039015.jpg) 存於 `public/ncu-campus-reference.jpg`，僅供視覺參考。圖片為透視繪製、沒有可確認的地理控制點，未做地理配準、未將圖上像素轉為經緯度；圖上可見行政大樓、圖書館、各學院、宿舍、運動場、校內通道及多個出口，名稱未無證據自動對應到 OSM 圖形。
- OSM 匯出中**零棟具高度標籤**，僅四棟具樓層數。GeoJSON 的 `height`、`min_height`、`height_source` 保留 `null`；有樓層數的建築只在渲染時用「每層 3 m」**推估顯示高度**，其餘無高度依據的建築以 6 m **純視覺示意高度**顯示。它們都不是實際高度。要得到可靠的真實高度，需要提供測量數據或附單棟來源的高度資料。
- `src/map/layers.js` 分開管理建築及道路圖層，並可依已整理公告標示能明確對應的施工建築；路燈、無障礙、安全及施工範圍 GeoJSON 仍未提供，不會虛構位置、故障狀態或路線。

## 更新 OSM 資料

下載前述 OSM API bbox 匯出為專案根目錄 `osm-campus.osm`，執行：

```sh
node scripts/import-osm.mjs osm-campus.osm public/data
```

腳本只讀取具封閉輪廓的建築 way 與 highway way，保持 OSM id、原始座標、名字、樓層與已明確標示單位為公尺的高度；不會捏造真實高度。更新後請複查資料來源時間與校園範圍。現有檔案尚未包含 multipolygon 建築 relation，也不會自動判定哪條道路可無障礙通行。

## 需補充的資料

請提供可授權使用、附 WGS84 位置的單棟建築高度／樓層資料、經測量的校園邊界與道路，以及對應官方導覽圖的地理控制點（若需要疊圖）。路燈、施工、無障礙及夜間安全圖層需各自附座標與資料來源。未取得這些資料前，勿將此原型用於導航或安全決策。
