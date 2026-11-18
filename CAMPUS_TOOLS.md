# 校園工具

## Windows 本機預覽

在專案根目錄安裝依賴。

~~~powershell
python -m venv frontend\.venv
.\frontend\.venv\Scripts\python.exe -m pip install -r backend\requirements-campus.txt
npm.cmd --prefix frontend ci
~~~

開兩個終端機。第一個在專案根目錄啟動後端。

~~~powershell
.\frontend\.venv\Scripts\python.exe backend\preview.py
~~~

第二個從專案根目錄進入 `frontend`，啟動前端。

~~~powershell
Set-Location frontend
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort
~~~

打開 [校園地圖](http://127.0.0.1:5173/campus)。左側「地圖標記」可顯示無障礙設施及審核公開的回報。「路線規劃」可選擇步行、避開已知障礙或優先照明。有道路封閉的公開回報會排除其附近 15 公尺內最接近的 OSM 路段。

前端與後端的本機預覽位址分別為 `127.0.0.1:5173` 與 `127.0.0.1:5000`。本機預覽網址使用 HTTP。

## 施工公告更新

預覽後端啟動時查一次校方公告，之後每 30 分鐘再查。已開啟的地圖每分鐘向本機後端讀取最新結果。「更新施工公告」可立即查詢。「校方施工公告」顯示來源、日期和最近成功查詢時間，沒有確認地圖位置的公告也能查看。

公告來自[總務處營繕組](https://www.oga.ncu.edu.tw/f3ec03a8)、[物理學系](https://www.phy.ncu.edu.tw/)和[體育室場地組](https://pe.ncu.edu.tw/category/11.html)。本機預覽直接讀取官方網站的公告，每次成功查詢會寫入 `backend/instance/construction-live.sqlite3`。舊有 `construction-live.json` 會在第一次啟動時匯入。來源連線失敗時保留該來源上次成功的結果。只有有明確工期及可辨識的單一建物且工期落在地圖兩週區間的公告會標紅。校方公告有更新時，須等下一次查詢才會出現在地圖上。

## 登入與回報

左側「管理後台」可開啟 [校園管理後台](http://127.0.0.1:5173/campus/admin)。選「預覽管理員」登入後，「使用者回報」可審核公開、退回、撤下標記、刪除回報及匯出 Excel。按「刪除回報」後再按「確認永久刪除」，會在同一筆交易內刪除資料庫中的回報及其舊有刪除紀錄，刪除後無法還原。舊版曾移至已刪除的回報會在後台標示為「待永久刪除」，可逐筆確認刪除。

「校方施工公告」可搜尋、隱藏及還原公告。隱藏的公告會從地圖公告列表及施工標記移除，自動更新後仍保留隱藏設定。

「登入與回報」提供兩個本機預覽角色。可先以「預覽回報者」送出回報，再登出並切換成「預覽管理員」審核。預覽回報資料存於 `backend/instance/preview-reports.sqlite3`。

地圖右側「回歸視角」會停止目前移動、恢復預設位置、縮放與角度，並清除建物選取及規劃路線。

右上方指北針可點擊或按 Enter，在平面與 3D 地圖之間切換。平面模式會朝北俯視，建物顯示為平面色塊；再次點擊可恢復先前的 3D 傾角及朝向。切換時保留路線與選取，平面模式的「回歸視角」仍維持平面。路線的圓形端點已標為「起點」與「終點」。淺色模式的側欄收合按鈕使用米黃色實心底及深色箭頭。

規劃完成後，右側地圖會顯示「清除路線」，側欄收起時仍可使用。它會清除路線及起終點圓形標記，保留其他圖層、目前視角與起終點選單，方便重新規劃。

點選地圖上的任一建物或左側建物清單，會放大並顯示該建物的名稱標籤；再點選同一建物、同一清單項目或名稱標籤，即取消選取並回到目前平面／3D 模式的預設視角。這項操作保留已規劃路線。窄螢幕選取時會自動收起側欄，讓建物與名稱有足夠的顯示空間。現有資料沒有名稱的建物會顯示「未命名建築」。

名稱使用專案原有建物資料；有 OSM 別名欄位時會一併顯示。圖書館的補充名稱及英文名另經[校方無障礙地圖](https://love.adm.ncu.edu.tw/NCU_counsel/NCU-barrier-free/)及[圖書館群介紹](https://www.ncu.edu.tw/p/412-1000-324.php?Lang=zh-tw)確認，標籤附來源連結。未確認的別名不會自行補上。

後台上方顯示全部、待審核、已公開、已退回四種真實回報數量。點擊統計卡片可篩選狀態，也可搜尋標題、內容、回報帳號、編號或類型。沒有回報與篩選無結果時會顯示不同說明，並提供返回地圖或清除篩選的入口。Excel 匯出包含所有狀態的回報，不受畫面篩選影響。

## 路線計算

每段道路使用 OSM 原始節點的經緯度估算公尺數。起終點投影至附近可連通的真實道路後，以 Dijkstra 演算法找出加權成本最低的路線；畫面距離是實際路段長度的加總。模式的偏好權重如下，這些倍率是程式設定，不是現場量測的通行時間或安全分數。

| 偏好 | 排除條件與成本 |
| --- | --- |
| 步行 | 排除不允許步行的路段，以路段公尺數作為成本。 |
| 輪椅／推行李 | 排除已標示的階梯、輪椅禁行、高路緣、超過 8.33% 的數字坡度、嚴重不平整路面及部分障礙；輪椅通行資訊未知的路段成本乘 1.5。 |
| 夜間 | 有照明標記的路段成本不變，照明未知乘 2，標記無照明乘 4。 |

三種模式都會避開審核公開的施工封路回報所對應的路段。未知標記不代表已確認可通行或有照明，入口與現場路況仍須確認。

## 啟用 Google 與中大 Portal

正式啟動使用 `flask --app app`（在 `backend/` 執行）或以 WSGI 對外提供 `app:app`。以同一個網站來源提供前端與 `/api`，並在後端程序環境設定下列變數。使用 Flask CLI 時也可由 `backend/.env` 載入。

| 變數 | 用途 |
| --- | --- |
| `CAMPUS_ORIGIN` | 使用者開啟的網站來源，例如 `https://campus.example.edu`。本機預設為 `http://127.0.0.1:5173`。 |
| `CAMPUS_SESSION_SECRET` | 工作階段簽章密鑰，可用 `python -c "import secrets; print(secrets.token_hex(32))"` 產生。 |
| `CAMPUS_GOOGLE_CLIENT_ID`、`CAMPUS_GOOGLE_CLIENT_SECRET` | Google Cloud Web 應用程式的 OpenID Connect 設定。回呼 URI 為網站來源加上 `/api/campus/callback/google`。 |
| `CAMPUS_PORTAL_CLIENT_ID`、`CAMPUS_PORTAL_CLIENT_SECRET` | 向國立中央大學電算中心申請的 Portal OpenID Connect 設定。回呼 URI 為網站來源加上 `/api/campus/callback/portal`。 |
| `CAMPUS_ADMINS` | 以逗號分隔的帳號白名單，格式為 `google:<sub>` 或 `portal:<sub>`。授權前先從本人瀏覽器的 `/api/campus/session` 確認經提供者驗證的 `account.subject`。 |
| `CAMPUS_REPORTS_DB` | 可選的 SQLite 路徑，預設為 `backend/instance/campus-reports.sqlite3`。 |

[Google OpenID Connect 設定](https://developers.google.com/identity/openid-connect/openid-connect) · [中大 Portal 介接說明](https://portal.ncu.edu.tw/about/howto)

## 地圖資料

- 無障礙標記採用 [國立中央大學無障礙地圖](https://love.adm.ncu.edu.tw/NCU_counsel/NCU-barrier-free/) 公開的 34 筆建物座標及設施項目。標記位於校方所列的建物參考點。入口、樓層與坡道的細部位置需查閱校方資料。
- 路線和地圖道路共用 [OpenStreetMap 校園範圍匯出](https://api.openstreetmap.org/api/0.6/map?bbox=121.1843596,24.9635065,121.1980519,24.9722322) 的路段、節點及通行屬性，路網取得日為 2026-11-18。建物參考點會投影至 120 公尺內的實際道路，最多比較比最近道路多 35 公尺的鄰近連通路網；已在道路上的點維持該路網。畫面顯示道路端點到建物參考點的距離，入口連接需現場確認。前端路線測試可在 `frontend/` 執行 `node --test tests/walkingRoutes.test.mjs`。[© OpenStreetMap contributors，ODbL](https://www.openstreetmap.org/copyright)
- 閒置設施標記來自管理員審核公開的回報，附回報及審核時間。初次啟動時圖層為空。

資料更新時可下載上述 NCU 網頁 HTML 與 OSM XML，再執行 `python frontend/scripts/import-campus-tools.py <ncu-html> <osm-xml>`。
