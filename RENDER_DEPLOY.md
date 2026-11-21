# Render Docker 部署與本機預覽

此專案以**單一 Docker Web Service** 提供 Vue 建置結果與 Flask `/api`；本地端仍可使用原本的 Vite + Flask 預覽，修改後先在本機驗證，再 push 到 GitHub 觸發 Render 部署。`render.yaml` 只宣告 Render **Free** Web Service，**不建立持久化磁碟或付費資料庫**。建立前仍應確認 Render 當時的方案與帳戶免費額度；不要在 Dashboard 將服務升級至付費方案。

## 本地修改與驗證（Windows PowerShell）

在專案根目錄安裝依賴（已安裝可略過）：

```powershell
python -m venv frontend\.venv
.\frontend\.venv\Scripts\python.exe -m pip install -r backend\requirements-campus.txt
npm.cmd --prefix frontend ci
```

開兩個終端機；第一個執行：

```powershell
.\frontend\.venv\Scripts\python.exe backend\preview.py
```

第二個執行：

```powershell
Set-Location frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

開啟 `http://127.0.0.1:5173/campus`。預覽資料只寫到本機，不會和 Render 的資料同步。提交前可執行：

```powershell
Set-Location frontend
npm.cmd run build
node --test tests/reportPlaces.test.mjs tests/walkingRoutes.test.mjs
Set-Location ..\backend
python -m unittest discover -s tests -v
```

若本機 Docker Desktop 已啟動，也可在**專案根目錄**檢查正式容器（不啟用預覽管理員；需要正式 OAuth 才能登入）：

```powershell
docker build -t intelligence-campus .
docker run --rm -p 10000:10000 -e CAMPUS_ORIGIN=http://127.0.0.1:10000 -e CAMPUS_SESSION_SECRET=local-container-test-secret -v campus-data:/data intelligence-campus
```

開啟 `http://127.0.0.1:10000/campus`。上述 Docker volume `campus-data` 只保留本機容器資料，不會同步到 Render。`docker run` 以 HTTP 供本機檢查，不應直接公開至網路。

## Render 首次部署

1. 將程式碼 push 到 GitHub；Render 只能讀取已 push 的提交，尚未提交的本機變更不會出現在 Render。**勿提交 `backend/.env`、本機 `instance`、密鑰或資料庫。**
2. 登入 [Render Dashboard](https://dashboard.render.com/) 並連接 GitHub repository。在 **New → Blueprint** 選擇這個 repo，Render 會讀取根目錄的 `render.yaml`；確認畫面顯示 **Free** Web Service、Docker、**沒有磁碟或其他付費資源**，才按建立。若 Render 畫面要求選擇付費方案，請取消，不要建立。Blueprint 會使用 `/health` 健康檢查。
3. 在 Render 的 `CAMPUS_ORIGIN` 提示中填入 Render 配發的**完整 HTTPS 網站來源**，例如 `https://intelligence-campus.onrender.com`（以 Dashboard 顯示的實際網址為準，結尾不加 `/`）。若首次建立時尚未知道最終網址，先完成建立後立即在該服務 **Environment** 中填正確網址、儲存並重新部署；未設定時容器會明確拒絕啟動，網址不一致也會使 CSRF／OAuth 失敗。`CAMPUS_SESSION_SECRET` 由 Blueprint 產生並應保持不變。
4. 若要使用 Google 登入，於 Render 服務 **Environment** 設定 `CAMPUS_GOOGLE_CLIENT_ID` 和 `CAMPUS_GOOGLE_CLIENT_SECRET`，並在 Google Cloud Console 將 `https://<你的網站>.onrender.com/api/campus/callback/google` 加入 OAuth 授權重新導向 URI。變更環境變數後重新部署。不要將 OAuth 密鑰放到 Dockerfile、`render.yaml` 或 GitHub。
5. 確認 `https://<你的網站>.onrender.com/health` 回傳 `{"status":"ok"}`，再檢查 `/campus`、`/campus/admin` 及 `/api/construction`。部署失敗時先看 Render 的 **Deploys / Logs**。後續 push 至服務連結的分支會自動重新建置 Docker image（除非自行關閉 auto-deploy）。

## 免費方案的資料、安全與使用限制

- `/data` 目前仍供回報 JSON、使用者 SQLite 和公告 SQLite 暫存使用，但 **Render Free 不支援持久化磁碟**。雲端服務在重啟或重新部署後，這些檔案可能全部消失；**勿把雲端回報或使用者權限當成可永久保存的資料**，也不要將此免費方案用於需要可靠留存資料的正式服務。本機資料不會因 Render 重啟受影響。
- 容器以非 root 的 `campus` 使用者執行 Gunicorn；啟動時會先準備容器內可寫的 `/data` 目錄，並不代表該目錄能跨部署保存。
- Free 服務在閒置後可能休眠，重新喚醒需等待；背景公告輪詢不能保證每 30 分鐘準時執行。請保持單一 Gunicorn worker，避免同一容器內重複輪詢。若未來需要持久化回報，須另行規劃可用的儲存方案，不能只靠目前的免費本機檔案。
- 雲端預覽管理員**不啟用**。正式站要送回報與管理需先設定 Google 登入；Google 已驗證的既有初始管理員機制仍由後端控制。
- 公告背景輪詢由 `CAMPUS_START_CONSTRUCTION_FEED=1` 啟動；正式站的管理員登入後可在施工公告面板手動更新官方來源（CSRF 驗證及更新鎖保護），一般訪客無法觸發；舊版 AI 更新端點仍停用。官方來源可能因網路限制或網站變更而無法擷取，舊成功結果仍會保留。
- 不要將本機 `backend/.env` 中的 `CAMPUS_ORIGIN=http://127.0.0.1:5173` 複製到 Render。若網址變更，須同步更改 `CAMPUS_ORIGIN` 及 OAuth 回呼 URI。Render 與本地資料彼此獨立。