# 中央大學 3D 校園地圖

首頁 `/` 使用 Vue 3、MapLibre GL JS、GeoJSON 與 OpenFreeMap 底圖顯示中央大學周邊的 OSM 建築輪廓、道路及 `fill-extrusion` 量體。原本未經測繪的 SVG 示意圖和其路線功能保留於 `/map`，**不可用於導航**。

## 啟動與檢查

```sh
npm install
npm run dev
npm run lint
npm run build
```

地圖底圖需網路連線；建築及道路 GeoJSON 已存放在 `public/data/`，無須瀏覽器對 Overpass 發送請求。拖曳平移、右鍵拖曳旋轉／傾斜、滾輪縮放，亦可使用右上角控制鈕。點建物或搜尋名稱可顯示資訊並高亮。位置與道路來自 OSM WGS84 資料，與底圖使用相同座標系統；OSM 資料不代表官方測繪成果。

## 資料與限制

- OSM 資料：[OpenStreetMap API bounding box 匯出](https://api.openstreetmap.org/api/0.6/map?bbox=121.18485,24.96505,121.19675,24.9717)，校園參考為 [OSM relation 18727079](https://www.openstreetmap.org/relation/18727079)。擷取日期 2026-11-09。轉成 128 個建築輪廓（71 個具名稱）、164 條道路／步道；資料授權 [ODbL](https://www.openstreetmap.org/copyright)，© OpenStreetMap contributors。此 bbox 涵蓋校園及鄰近區域，**不是正式校園邊界裁切**，因此部分輪廓及道路位於校外。
- [中央大學官方校園導覽圖片](https://www.ncu.edu.tw/var/file/0/1000/img/3/712039015.jpg) 存於 `public/ncu-campus-reference.jpg`，僅供視覺參考。圖片為透視繪製、沒有可確認的地理控制點，未做地理配準、未將圖上像素轉為經緯度；圖上可見行政大樓、圖書館、各學院、宿舍、運動場、校內通道及多個出口，名稱未無證據自動對應到 OSM 圖形。
- OSM 匯出中**零棟具高度標籤**，僅四棟具樓層數。GeoJSON 的 `height`、`min_height`、`height_source` 保留 `null`；有樓層數的建築只在渲染時用「每層 3 m」**推估顯示高度**，其餘無高度依據的建築以 6 m **純視覺示意高度**顯示。它們都不是實際高度。要得到可靠的真實高度，需要提供測量數據或附單棟來源的高度資料。
- `src/map/layers.js` 分開管理建築及道路圖層，預留路燈、施工、無障礙、安全資料集合；這些資料目前尚未提供，不會虛構位置、故障狀態或路線。

## 更新 OSM 資料

下載前述 OSM API bbox 匯出為專案根目錄 `osm-campus.osm`，執行：

```sh
node scripts/import-osm.mjs osm-campus.osm public/data
```

腳本只讀取具封閉輪廓的建築 way 與 highway way，保持 OSM id、原始座標、名字、樓層與已明確標示單位為公尺的高度；不會捏造真實高度。更新後請複查資料來源時間與校園範圍。現有檔案尚未包含 multipolygon 建築 relation，也不會自動判定哪條道路可無障礙通行。

## 需補充的資料

請提供可授權使用、附 WGS84 位置的單棟建築高度／樓層資料、經測量的校園邊界與道路，以及對應官方導覽圖的地理控制點（若需要疊圖）。路燈、施工、無障礙及夜間安全圖層需各自附座標與資料來源。未取得這些資料前，勿將此原型用於導航或安全決策。
