<template>
  <main class="campus-page">
    <header class="header">
      <div class="identity">
        <span class="mark">中</span
        ><span
          ><strong>國立中央大學</strong
          ><small>NATIONAL CENTRAL UNIVERSITY</small></span
        >
      </div>
      <nav aria-label="頁面導覽">
        <span>3D OSM 建築輪廓地圖</span
        ><RouterLink to="/map">原有校園示意圖 ↗</RouterLink>
      </nav>
    </header>
    <div class="page-body">
      <aside class="sidebar">
        <div class="eyebrow">NCU CAMPUS / OPENSTREETMAP</div>
        <h1>從真實輪廓，<br /><em>探索中大。</em></h1>
        <p>
          建築輪廓與道路取自 OpenStreetMap，採 WGS84
          經緯度與底圖對齊。滑鼠拖曳平移、右鍵拖曳旋轉與傾斜，滾輪縮放；亦可使用地圖右上角控制鈕。
        </p>
        <label class="search-label" for="building-search"
          >搜尋 OSM 建築名稱</label
        >
        <input
          id="building-search"
          v-model="query"
          type="search"
          placeholder="搜尋建築…"
        />
        <div class="list" aria-label="OSM 已命名建築">
          <button
            v-for="building in filteredBuildings"
            :key="building.properties.id"
            class="building-row"
            :class="{ active: selectedId === building.properties.id }"
            type="button"
            @click="selectedId = building.properties.id"
          >
            {{ building.properties.name }} <span aria-hidden="true">↗</span>
          </button>
          <p v-if="!filteredBuildings.length" class="empty">
            {{ buildings.length ? "找不到符合的建築" : "載入建築資料中…" }}
          </p>
        </div>
        <div v-if="selectedBuilding" class="details" aria-live="polite">
          <span class="eyebrow">BUILDING / 建築資訊</span>
          <h2>{{ selectedBuilding.properties.name || "未命名建築" }}</h2>
          <p>高度：{{ heightDescription(selectedBuilding.properties) }}</p>
          <p>
            樓層：{{
              selectedBuilding.properties.building_levels ?? "OSM 未提供"
            }}
          </p>
          <a
            :href="selectedBuilding.properties.osm_url"
            target="_blank"
            rel="noopener noreferrer"
            >在 OpenStreetMap 檢視資料 ↗</a
          >
        </div>
        <div class="notice">
          灰色建築的 6
          公尺<strong>僅為顯示輪廓的示意高度</strong>，不是實際量測。綠色建築為
          OSM 樓層數 × 每層 3
          公尺推估，亦非實測。沒有控制點，官方透視導覽圖不疊在地理底圖上。
        </div>
        <a
          class="reference"
          :href="`${baseUrl}ncu-campus-reference.jpg`"
          target="_blank"
          rel="noopener noreferrer"
          >查看中央大學官方校園導覽圖片 ↗</a
        >
      </aside>
      <section class="viewer" aria-label="中央大學 3D 地理地圖">
        <div class="viewer-top">
          <span>● &nbsp;互動式校園地圖</span
          ><span>OSM GEOJSON / MAPLIBRE GL JS</span>
        </div>
        <div class="map-area">
          <CampusMap
            :selected-id="selectedId"
            @loaded="onLoaded"
            @select="selectedId = $event"
          />
        </div>
        <div class="viewer-bottom">
          <span>{{ buildings.length }} 個建築輪廓 · 道路與步道圖層</span
          ><span>高度不足處以示意量體呈現</span>
        </div>
      </section>
    </div>
    <footer>
      NCU CAMPUS · 3D MAP
      <span>© OpenStreetMap contributors (ODbL) · OpenFreeMap 底圖</span>
    </footer>
  </main>
</template>
<script setup>
import { computed, ref } from "vue";
import CampusMap from "../components/CampusMap.vue";
const baseUrl = import.meta.env.BASE_URL;
const buildings = ref([]);
const selectedId = ref("");
const query = ref("");
const filteredBuildings = computed(() =>
  buildings.value
    .filter((feature) =>
      feature.properties.name
        ?.toLowerCase()
        .includes(query.value.trim().toLowerCase())
    )
    .sort((a, b) =>
      a.properties.name.localeCompare(b.properties.name, "zh-Hant")
    )
);
const selectedBuilding = computed(() =>
  buildings.value.find((feature) => feature.properties.id === selectedId.value)
);
function onLoaded(features) {
  buildings.value = features;
}
function heightDescription(properties) {
  if (properties.height !== null)
    return `${properties.height} 公尺（OSM 高度標籤）`;
  if (properties.building_levels !== null)
    return `OSM 未提供；視覺推估約 ${properties.building_levels * 3} 公尺（${
      properties.building_levels
    } 層 × 3 公尺）`;
  return "未知（地圖以 6 公尺示意顯示，不代表真實高度）";
}
</script>
<style scoped>
.campus-page {
  min-height: 100vh;
  background: #f7f8f4;
  color: #20372d;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  min-height: 82px;
  padding: 12px max(4vw, 22px);
  border-bottom: 1px solid #e2e9df;
  background: white;
}
.identity {
  display: flex;
  align-items: center;
  gap: 12px;
}
.identity strong,
.identity small {
  display: block;
}
.identity strong {
  font-size: 15px;
  letter-spacing: 0.06em;
}
.identity small {
  font-size: 9px;
  color: #819788;
  letter-spacing: 0.12em;
}
.mark {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 8px;
  background: #285743;
  color: white;
  font-size: 21px;
}
nav {
  display: flex;
  gap: 22px;
  font-size: 12px;
}
nav a,
.reference,
.details a {
  color: #285743;
}
.page-body {
  display: grid;
  grid-template-columns: minmax(270px, 340px) minmax(0, 1fr);
  gap: 28px;
  max-width: 1700px;
  margin: auto;
  padding: 36px max(4vw, 22px);
}
.sidebar h1 {
  font-size: clamp(32px, 3vw, 46px);
  line-height: 1.3;
  letter-spacing: -0.04em;
}
.sidebar h1 em {
  color: #568467;
  font-style: normal;
}
.sidebar > p {
  font-size: 13px;
  line-height: 1.9;
  color: #647d6a;
}
.eyebrow {
  font-size: 10px;
  letter-spacing: 0.12em;
  font-weight: 700;
  color: #689076;
}
.search-label {
  display: block;
  margin-top: 25px;
  margin-bottom: 8px;
  font-weight: 700;
  font-size: 13px;
}
input {
  width: 100%;
  border: 1px solid #cbd8cc;
  padding: 11px;
  border-radius: 8px;
  background: white;
}
.list {
  overflow-y: auto;
  max-height: 260px;
  margin: 8px 0 15px;
  border: 1px solid #e2e9df;
  border-radius: 8px;
  background: white;
}
.building-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border: 0;
  border-bottom: 1px solid #eef1ea;
  background: white;
  color: #314b3b;
  text-align: left;
  cursor: pointer;
}
.building-row:hover,
.building-row.active {
  background: #e4eee1;
}
.empty {
  padding: 10px;
  font-size: 12px;
}
.details {
  padding: 15px;
  background: white;
  border: 1px solid #dfe9dc;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.6;
}
.details h2 {
  margin: 8px 0;
  font-size: 18px;
}
.details a {
  overflow-wrap: anywhere;
}
.notice {
  padding: 12px;
  margin: 15px 0;
  background: #eef3e9;
  border-radius: 8px;
  color: #4f674f;
  font-size: 11px;
  line-height: 1.8;
}
.reference {
  font-size: 12px;
}
.viewer {
  overflow: hidden;
  min-width: 0;
  border-radius: 15px;
  border: 1px solid #dfe9dc;
  background: white;
  box-shadow: 0 24px 50px #26493318;
}
.viewer-top,
.viewer-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 49px;
  padding: 12px 18px;
  color: #3b6248;
  font-size: 11px;
  font-weight: 700;
}
.viewer-top span:last-child,
.viewer-bottom {
  color: #819184;
  font-size: 10px;
  letter-spacing: 0.06em;
}
.map-area {
  height: min(73vh, 780px);
  min-height: 450px;
}
footer {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  max-width: 1700px;
  margin: auto;
  padding: 10px max(4vw, 22px) 28px;
  color: #9ba99d;
  font-size: 10px;
}
@media (max-width: 900px) {
  .page-body {
    grid-template-columns: 1fr;
  }
  .sidebar h1 br {
    display: none;
  }
  .map-area {
    height: 65vh;
  }
}
@media (max-width: 520px) {
  .header {
    align-items: flex-start;
    flex-direction: column;
  }
  nav {
    justify-content: space-between;
    width: 100%;
  }
  .page-body {
    padding: 22px 14px;
    gap: 20px;
  }
  .map-area {
    min-height: 480px;
  }
  .viewer-top span:last-child,
  .viewer-bottom span:last-child {
    display: none;
  }
  footer {
    flex-direction: column;
  }
}
</style>
