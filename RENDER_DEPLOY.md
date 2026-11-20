# Render Docker 部署與本機預覽

此專案以**單一 Docker Web Service** 提供 Vue 建置結果與 Flask `/api`；本地端仍可使用原本的 Vite + Flask 預覽，修改後先在本機驗證，再 push 到 GitHub 觸發 Render 部署。此方案會使用 Render **付費** Web Service 及持久化磁碟；建立服務前請先查看 [Render 定價](https://render.com/pricing)。

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
2. 登入 [Render Dashboard](https://dashboard.render.com/) 並連接 GitHub repository。在 **New → Blueprint** 選擇這個 repo，Render 會讀取根目錄的 `render.yaml`；請先檢查服務／磁碟費用再確認建立。此 Blueprint 設為 Docker、付費 `starter` 方案、單一服務、`/data` 持久化磁碟與 `/health` 健康檢查。
3. 在 Render 的 `CAMPUS_ORIGIN` 提示中填入 Render 配發的**完整 HTTPS 網站來源**，例如 `https://intelligence-campus.onrender.com`（以 Dashboard 顯示的實際網址為準，結尾不加 `/`）。若首次建立時尚未知道最終網址，先完成建立後立即在該服務 **Environment** 中填正確網址、儲存並重新部署；未設定時容器會明確拒絕啟動，網址不一致也會使 CSRF／OAuth 失敗。`CAMPUS_SESSION_SECRET` 由 Blueprint 產生並應保持不變。
4. 若要使用 Google 登入，於 Render 服務 **Environment** 設定 `CAMPUS_GOOGLE_CLIENT_ID` 和 `CAMPUS_GOOGLE_CLIENT_SECRET`，並在 Google Cloud Console 將 `https://<你的網站>.onrender.com/api/campus/callback/google` 加入 OAuth 授權重新導向 URI。Portal 登入同理使用 `CAMPUS_PORTAL_CLIENT_ID`、`CAMPUS_PORTAL_CLIENT_SECRET` 與 `/api/campus/callback/portal`。變更環境變數後重新部署。不要將 OAuth 密鑰放到 Dockerfile、`render.yaml` 或 GitHub。
5. 確認 `https://<你的網站>.onrender.com/health` 回傳 `{"status":"ok"}`，再檢查 `/campus`、`/campus/admin` 及 `/api/construction`。部署失敗時先看 Render 的 **Deploys / Logs**。後續 push 至服務連結的分支會自動重新建置 Docker image（除非自行關閉 auto-deploy）。

## 資料、安全與費用限制

- `/data` 儲存回報 JSON、使用者 SQLite、公告 SQLite；掛載磁碟僅在執行時可用，部署、重啟後資料仍在。**Render Free 服務無法掛載持久化磁碟**；若改用 Free，資料會在重啟或部署後消失，不適合正式回報功能。
- 容器啟動時先設定 `/data` 目錄權限，再以非 root 的 `campus` 使用者執行 Gunicorn；若已有其他使用者寫入磁碟並變更子檔案權限，須先在 Render Shell 修正檔案擁有者。
- 請保持**單一服務執行個體／單一 Gunicorn worker**，不可讓多台容器同時讀寫 SQLite。含磁碟的服務無法水平擴充且部署時可能短暫中斷。定期備份 `/data`；程式更新不等於資料備份。
- 雲端預覽管理員**不啟用**。正式站要送回報與管理需先設定 Google／Portal 登入；Google 已驗證的既有初始管理員機制仍由後端控制。
- 公告背景輪詢由 `CAMPUS_START_CONSTRUCTION_FEED=1` 啟動；正式站舊版 AI 更新端點停用且前端不顯示手動更新按鈕。官方來源可能因網路限制或網站變更而無法擷取，舊成功結果仍會保留。
- 不要將本機 `backend/.env` 中的 `CAMPUS_ORIGIN=http://127.0.0.1:5173` 複製到 Render。若網址變更，須同步更改 `CAMPUS_ORIGIN` 及 OAuth 回呼 URI。Render 與本地資料彼此獨立。