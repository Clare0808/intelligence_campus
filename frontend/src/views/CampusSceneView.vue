<template>
  <main class="campus-page">
    <!-- <header class="header">
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
    </header> -->
    <div class="page-body">
      <section class="viewer" aria-label="中央大學 3D 地理地圖">
        <div class="map-area">
          <CampusMap
            :selected-id="selectedId"
            @loaded="onLoaded"
            @select="onSelect"
          />
        </div>
      </section>
      <aside
        id="building-sidebar"
        class="sidebar"
        :class="{ 'sidebar-closed': !sidebarOpen }"
        aria-label="OSM 建築搜尋側邊欄"
        :inert="!sidebarOpen"
      >
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
            @click="onSelect(building.properties.id)"
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
        <a
          class="reference"
          :href="`${baseUrl}ncu-campus-reference.jpg`"
          target="_blank"
          rel="noopener noreferrer"
          >查看中央大學官方校園導覽圖片 ↗</a
        >
      </aside>
      <button
        class="sidebar-toggle"
        :class="{ 'sidebar-toggle-closed': !sidebarOpen }"
        type="button"
        :aria-label="sidebarOpen ? '收起建築搜尋側邊欄' : '展開建築搜尋側邊欄'"
        aria-controls="building-sidebar"
        :aria-expanded="sidebarOpen"
        @click="sidebarOpen = !sidebarOpen"
      >
        {{ sidebarOpen ? "‹" : "›" }}
      </button>
    </div>
  </main>
</template>
<script setup>
import { computed, ref } from "vue";
import CampusMap from "../components/CampusMap.vue";
const baseUrl = import.meta.env.BASE_URL;
const buildings = ref([]);
const selectedId = ref("");
const query = ref("");
const sidebarOpen = ref(true);
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
function onSelect(id) {
  selectedId.value = id;
  sidebarOpen.value = true;
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
  height: 100vh;
  height: 100dvh;
  background: #f7f8f4;
  color: #20372d;
}
.reference,
.details a {
  color: #285743;
}
.page-body {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}
.sidebar {
  position: absolute;
  z-index: 2;
  top: 16px;
  bottom: 16px;
  left: 16px;
  width: min(340px, calc(100% - 56px));
  overflow-y: auto;
  padding: 20px;
  border: 1px solid #dfe9dc;
  border-radius: 12px;
  background: #f7f8f4;
  box-shadow: 0 12px 35px #26493338;
  transition: transform 0.25s ease, visibility 0.25s ease;
}
.sidebar-closed {
  visibility: hidden;
  transform: translateX(calc(-100% - 16px));
}
.sidebar-toggle {
  border: 1px solid #dfe9dc;
  background: white;
  color: #285743;
  cursor: pointer;
  position: absolute;
  z-index: 3;
  top: 50%;
  left: calc(16px + min(340px, 100% - 56px));
  width: 32px;
  height: 56px;
  transform: translateY(-50%);
  border-radius: 0 8px 8px 0;
  box-shadow: 4px 2px 12px #26493326;
  font-size: 26px;
  transition: left 0.25s ease;
}
.sidebar-toggle-closed {
  left: 0;
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
  max-height: min(260px, 35vh);
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
  position: relative;
  width: 100%;
  height: 100%;
  background: white;
}
.viewer-top,
.viewer-bottom {
  position: absolute;
  z-index: 1;
  right: 16px;
  padding: 9px 12px;
  border-radius: 8px;
  background: #ffffffed;
  color: #3b6248;
  font-size: 11px;
  font-weight: 700;
  pointer-events: none;
}
.viewer-top {
  top: 16px;
  right: 65px;
}
.viewer-bottom {
  bottom: 32px;
  color: #819184;
  font-size: 10px;
}
.map-area {
  width: 100%;
  height: 100%;
}
@media (max-width: 520px) {
  .sidebar {
    top: 8px;
    bottom: 8px;
    left: 8px;
    width: min(340px, calc(100% - 48px));
  }
  .sidebar-toggle {
    left: calc(8px + min(340px, 100% - 48px));
  }
  .sidebar-toggle-closed {
    left: 0;
  }
  .viewer-top,
  .viewer-bottom {
    display: none;
  }
  .list {
    max-height: 30vh;
  }
}
</style>
